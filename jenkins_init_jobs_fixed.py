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
import sys
import time
import requests
from requests.auth import HTTPBasicAuth

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "admin")
WORKSPACE = os.getenv("WORKSPACE", "/workspace")
JENKINS_ENV_FILE = os.getenv("JENKINS_ENV_FILE", "/workspace/jenkins.env")
PIPELINE_DIR = os.getenv("PIPELINE_DIR", "/workspace/pipelines")
OUTPUT_ENV = os.path.join(WORKSPACE, ".env")

session = requests.Session()
session.auth = HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)

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
        headers = {'Content-Type': 'application/json'}
        headers.update(get_crumb_headers())
        endpoint = f"{JENKINS_URL}/user/{JENKINS_USER}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken"
        payload = {'newTokenName': token_name}
        r = session.post(endpoint, headers=headers, json=payload, timeout=10)
        if r.status_code in (200, 201):
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
            except ValueError:
                pass
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

def load_pipelines():
    jobs = []
    if not os.path.exists(PIPELINE_DIR):
        print(f"⚠️ No pipelines folder found at {PIPELINE_DIR}")
        return jobs
    for file in os.listdir(PIPELINE_DIR):
        if file.endswith(".groovy"):
            with open(os.path.join(PIPELINE_DIR, file)) as f:
                script = f.read()
            jobs.append({
                "name": file.replace(".groovy", ""),
                "script": script
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
    print(f"Jenkins URL: {JENKINS_URL}")
    if not wait_for_jenkins():
        sys.exit(1)
    print("\nGenerating API token for admin user (optional)...")
    token = create_api_token()
    if token:
        print("✓ Generated API token for admin user")
    else:
        print("⚠️ Could not generate API token; continuing with configured token")
    write_env_files(token)
    
    # Create default jobs from repository scripts if available
    print("\nCreating default Jenkins jobs from repository scripts...")
    # Map job names to script files placed under <workspace>/jenkins/
    job_script_map = {
        "API-Health-Check": "api_healcheck.groovy",
        "Yahoo-Stock-Scraper": "yahoo_scraper.groovy",
        "Git-Repository-Clone": "git_repo_clone.groovy",
    }

    for job_name, script_file in job_script_map.items():
        script_path = os.path.join(WORKSPACE, "jenkins", script_file)
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r') as sf:
                    script = sf.read()
                xml = create_pipeline_xml(script)
                print(f"Creating job from script: {job_name} <- {script_file}")
                create_job(job_name, xml)
            except Exception as e:
                print(f"✗ Failed to read/create job {job_name} from {script_file}: {e}")
        else:
            print(f"⚠️ Script not found for {job_name} at {script_path}; skipping. You can add the script to {os.path.join(WORKSPACE, 'jenkins')} and restart this init container.")
    
    # Create jobs from folder if present
    print("\nCreating pipeline jobs from folder if present...")

    
    # Create jobs from folder if present
    print("\nCreating pipeline jobs from folder if present...")
    jobs = load_pipelines()
    for job in jobs:
        xml = create_pipeline_xml(job["script"])
        create_job(job["name"], xml)
    
    print("\n✓ Jenkins job initialization complete")
    sys.exit(0)

if __name__ == "__main__":
    main()
