#!/usr/bin/env python3
"""
Robust Jenkins initialization script for container automation.
- Waits for Jenkins API to be ready
- Obtains CSRF crumb
- Generates API token for admin user (if possible)
- Writes credentials to /workspace/.env and to JENKINS_ENV_FILE
- Creates pipeline jobs from /workspace/pipelines if present using XML flow-definition
- Logs meaningful messages, exits 0 on success, non-zero on fatal errors
"""
import os
import re
import sys
import time
import requests
from requests.auth import HTTPBasicAuth

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "admin")
JENKINS_TOKEN_FILE = os.getenv("JENKINS_TOKEN_FILE", "/var/jenkins_home/jenkins_token.txt")
WORKSPACE = os.getenv("WORKSPACE", "/workspace")
JENKINS_ENV_FILE = os.getenv("JENKINS_ENV_FILE", "/workspace/jenkins.env")
PIPELINE_DIR = os.getenv("PIPELINE_DIR", "/workspace/Jenkins")
OUTPUT_ENV = os.path.join(WORKSPACE, ".env")

CANONICAL_JOB_NAME_MAP = {
    "api_healcheck.groovy": "API-Health-Check",
    "yahoo_scraper.groovy": "Yahoo-Stock-Scraper",
    "git_repo_clone.groovy": "Git-Repository-Clone",
}

session = requests.Session()


def init_session_auth(token=None):
    token_to_use = token if token is not None else JENKINS_TOKEN
    session.auth = HTTPBasicAuth(JENKINS_USER, token_to_use)


def read_existing_token_file():
    try:
        if os.path.exists(JENKINS_TOKEN_FILE):
            with open(JENKINS_TOKEN_FILE, "r") as f:
                token = f.read().strip()
            if token:
                print(f"✓ Found Jenkins token file at {JENKINS_TOKEN_FILE}")
                return token
    except Exception as e:
        print(f"⚠️ Could not read Jenkins token file: {e}")
    return None


init_session_auth()

def wait_for_jenkins(timeout=300):
    print(f"Waiting for Jenkins at {JENKINS_URL} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = session.get(f"{JENKINS_URL}/api/json", timeout=5)
            if r.status_code == 200:
                print("✓ Jenkins is ready")
                return True
        except Exception:
            pass
        time.sleep(5)
    print("✗ Jenkins did not start within timeout")
    return False

def get_crumb_headers():
    try:
        r = session.get(f"{JENKINS_URL}/crumbIssuer/api/json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            field = data.get('crumbRequestField')
            crumb = data.get('crumb')
            if field and crumb:
                return {field: crumb}
    except Exception:
        pass
    return {}

def create_api_token(token_name='init-token'):
    try:
        headers = {}
        headers.update(get_crumb_headers())
        endpoint = f"{JENKINS_URL}/user/{JENKINS_USER}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken"
        payload = {'newTokenName': token_name}
        r = session.post(endpoint, headers=headers, data=payload, timeout=10)
        if r.status_code not in (200, 201):
            print(f"✗ Token generation failed: {r.status_code} - {r.text[:300]}")
            return None
        try:
            data = r.json()
            def find_token(d):
                if isinstance(d, dict):
                    for k, v in d.items():
                        if k == 'tokenValue':
                            return v
                        else:
                            res = find_token(v)
                            if res:
                                return res
                return None
            token = find_token(data)
            if token:
                return token
            print(f"✗ Token generation response did not contain tokenValue: {r.text[:300]}")
        except ValueError:
            print(f"✗ Token generation returned non-JSON response: {r.text[:300]}")
    except Exception as e:
        print(f"Warning: could not create API token: {e}")
    return None

def write_env_files(token_value=None):
    lines = [
        f"JENKINS_URL={JENKINS_URL}",
        f"JENKINS_USER={JENKINS_USER}",
        f"JENKINS_TOKEN={token_value if token_value else JENKINS_TOKEN}"
    ]
    content = "\n".join(lines) + "\n"
    try:
        with open(OUTPUT_ENV, 'w') as f:
            f.write(content)
        print(f"✓ Wrote credentials to {OUTPUT_ENV}")
    except Exception as e:
        print(f"✗ Failed to write {OUTPUT_ENV}: {e}")
    try:
        with open(JENKINS_ENV_FILE, 'w') as f:
            f.write(content)
        print(f"✓ Wrote credentials to {JENKINS_ENV_FILE}")
    except Exception as e:
        print(f"✗ Failed to write {JENKINS_ENV_FILE}: {e}")

def normalize_job_name(name):
    base_name = os.path.basename(name)
    if base_name in CANONICAL_JOB_NAME_MAP:
        return CANONICAL_JOB_NAME_MAP[base_name]

    segments = re.split(r"[_\-\s]+", name)
    return "-".join([segment.capitalize() for segment in segments if segment])


def job_exists(name):
    try:
        r = session.get(f"{JENKINS_URL}/job/{name}/api/json", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def delete_job(name):
    headers = get_crumb_headers()
    headers.update({"Content-Type": "application/x-www-form-urlencoded"})
    try:
        r = session.post(
            f"{JENKINS_URL}/job/{name}/doDelete",
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        if r.status_code in (200, 302):
            print(f"✓ Deleted legacy duplicate job: {name}")
            return True
        print(f"⚠️ Failed to delete legacy duplicate job {name}: {r.status_code}")
    except Exception as e:
        print(f"⚠️ Error deleting legacy duplicate job {name}: {e}")
    return False


def load_groovy_jobs():
    jobs = []
    if not os.path.isdir(PIPELINE_DIR):
        print(f"⚠️ No Jenkins job folder found at {PIPELINE_DIR}")
        return jobs

    for root, dirs, files in os.walk(PIPELINE_DIR):
        dirs[:] = [d for d in dirs if d != "init.groovy.d"]
        for file in files:
            if not file.endswith(".groovy"):
                continue
            if file.startswith("init"):
                continue

            script_path = os.path.join(root, file)
            try:
                with open(script_path, "r") as sf:
                    script = sf.read()
            except Exception as e:
                print(f"⚠️ Failed to read {script_path}: {e}")
                continue

            rel_path = os.path.relpath(script_path, PIPELINE_DIR)
            raw_name = os.path.splitext(rel_path)[0].replace(os.sep, "-")
            job_name = normalize_job_name(raw_name)
            legacy_names = []
            raw_basename = os.path.splitext(file)[0]
            if raw_basename != job_name:
                legacy_names.append(raw_basename)

            jobs.append({
                "name": job_name,
                "script": script,
                "path": script_path,
                "legacy_names": legacy_names,
            })

    return jobs

def create_pipeline_xml(script):
    return f"""<?xml version='1.1' encoding='UTF-8'?>\n<flow-definition plugin='workflow-job'>\n  <definition class='org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition' plugin='workflow-cps'>\n    <script><![CDATA[{script}]]></script>\n    <sandbox>true</sandbox>\n  </definition>\n</flow-definition>"""

def create_job(name, xml):
    try:
        r = session.get(f"{JENKINS_URL}/job/{name}/api/json", timeout=5)
        if r.status_code == 200:
            print(f"✓ Job already exists: {name}")
            return True
    except Exception:
        pass
    headers = get_crumb_headers()
    headers.update({"Content-Type": "application/xml"})
    try:
        r = session.post(
            f"{JENKINS_URL}/createItem",
            params={"name": name},
            data=xml.encode('utf-8'),
            headers=headers,
            timeout=10
        )
        if r.status_code in (200, 201):
            print(f"✓ Created job: {name}")
            return True
        else:
            print(f"✗ Failed to create {name}: {r.status_code} - {r.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Error creating {name}: {e}")
        return False

def main():
    global JENKINS_TOKEN

    print(f"Jenkins URL: {JENKINS_URL}")
    if not wait_for_jenkins():
        sys.exit(1)

    existing_token = read_existing_token_file()
    if existing_token:
        JENKINS_TOKEN = existing_token
        init_session_auth(JENKINS_TOKEN)
        print("✓ Using existing Jenkins-generated token")
    else:
        print("\nGenerating API token for admin user (optional)...")
        token = create_api_token()
        if token:
            print("✓ Generated API token for admin user")
            JENKINS_TOKEN = token
            init_session_auth(JENKINS_TOKEN)
        else:
            print("⚠️ Could not generate API token; continuing with configured token")
            init_session_auth(JENKINS_TOKEN)

    write_env_files(JENKINS_TOKEN)

    print("\nCreating Jenkins jobs from repository groovy files...")
    jobs = load_groovy_jobs()
    if not jobs:
        print(f"⚠️ No groovy job scripts found in {PIPELINE_DIR}")
    for job in jobs:
        xml = create_pipeline_xml(job["script"])
        print(f"Creating job from script: {job['name']} ({job['path']})")
        created = create_job(job["name"], xml)
        if created and job.get("legacy_names"):
            for legacy_name in job["legacy_names"]:
                if legacy_name != job["name"] and job_exists(legacy_name):
                    delete_job(legacy_name)

    print("\n✓ Jenkins job initialization complete")
    sys.exit(0)

if __name__ == "__main__":
    main()
