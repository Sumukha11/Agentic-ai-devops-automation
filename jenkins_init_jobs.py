#!/usr/bin/env python3
"""
Enhanced Jenkins init script:
- Fetches Jenkins CSRF crumb and includes it in job creation requests
- Generates an API token for the admin user and writes JENKINS_API_TOKEN to /workspace/.env
- Writes .env to project root (docker-compose mounts project to /workspace)
"""
import requests
import time
import sys
import os
import json
from requests.auth import HTTPBasicAuth

PIPELINE_DIR = "/workspace/pipelines"
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "admin")
WORKSPACE = os.getenv("WORKSPACE", "/workspace")
OUTPUT_ENV = os.path.join(WORKSPACE, ".env")

session = requests.Session()
session.auth = HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)

def load_pipelines():
    jobs = []

    if not os.path.exists(PIPELINE_DIR):
        print("⚠️ No pipelines folder found")
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
    return f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script><![CDATA[{script}]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""

jobs = [
    {
        "name": "API-Health-Check",
        "description": "Check health of critical APIs",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Check health of critical APIs</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Health Check") {
            steps {
                sh "echo Checking API health..."
                sh "curl -I https://www.google.com || true"
                sh "curl -I https://api.github.com || true"
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    },
    {
        "name": "Yahoo-Stock-Scraper",
        "description": "Fetch stock prices from Yahoo Finance",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Fetch stock prices from Yahoo Finance</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Fetch Stock") {
            steps {
                sh "echo Fetching stock data for AAPL..."
                sh "python3 -c \"import yfinance as yf; stock = yf.Ticker('AAPL'); print(stock.info.get('currentPrice', 'N/A'))\""
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    },
    {
        "name": "Git-Repository-Clone",
        "description": "Clone a git repository",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Clone a git repository</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Clone") {
            steps {
                echo "Clone Repository Stage"
                sh "echo Configure this job with a git repository URL"
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    }
]


def wait_for_jenkins(timeout=300):
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
    """Return dict of crumb header to include for CSRF protection. Empty dict if not available."""
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
    """Generate an API token for the configured user via Jenkins API.
    Returns token value string on success, or None.
    """
    try:
        headers = {'Content-Type': 'application/json'}
        headers.update(get_crumb_headers())
        endpoint = f"{JENKINS_URL}/user/{JENKINS_USER}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken"
        payload = {'newTokenName': token_name}
        r = session.post(endpoint, headers=headers, json=payload, timeout=10)
        if r.status_code in (200, 201):
            try:
                data = r.json()
                # Jenkins may nest token under 'data' or return tokenValue directly
                # Search for tokenValue recursively
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
        print("Warning: could not create API token:", e)
    return None


def write_env_file(token_value=None):
    with open("/workspace/.env", "w") as f:
        f.write(f"JENKINS_URL={JENKINS_URL}\n")
        f.write(f"JENKINS_USER={JENKINS_USER}\n")
        f.write(f"JENKINS_TOKEN={token_value}\n")
        if token_value:
            lines.append(f"JENKINS_API_TOKEN={token_value}")
        content = "\n".join(lines) + "\n"
        os.makedirs(os.path.dirname(OUTPUT_ENV), exist_ok=True)
        with open(OUTPUT_ENV, 'w') as f:
            f.write(content)
        print(f"✓ Wrote credentials to {OUTPUT_ENV}")



def create_job(name, xml):
    """Create a job via Jenkins API, using crumb header if available."""
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


if __name__ == "__main__":
    print(f"Jenkins URL: {JENKINS_URL}")
    print(f"Waiting for Jenkins to be ready...")

    if not wait_for_jenkins():
        sys.exit(1)

    # Try to create an API token and persist it to the project's .env so later services
    # or subsequent docker-compose runs can pick it up.
    print("\nGenerating API token for admin user (optional)...")
    token = create_api_token()
    if token:
        print("✓ Generated API token for admin user")
    else:
        print("⚠️ Could not generate API token; continuing without it")

    # Persist credentials to /workspace/.env (project root should be mounted)
    write_env_file(token)

print("\nCreating pipeline jobs from folder...")

for job in load_pipelines():
    xml = create_pipeline_xml(job["script"])
    create_job(job["name"], xml)
    print("\n✓ Job initialization complete")

import requests
import time
import sys
import os
from requests.auth import HTTPBasicAuth

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")
JENKINS_ENV_FILE = os.getenv("JENKINS_ENV_FILE", "/workspace/jenkins.env")

session = requests.Session()


def generate_and_write_api_token(initial_token):
    """Generate a new Jenkins API token for JENKINS_USER and write it to the mounted env file."""
    try:
        # Get CSRF crumb if available
        headers = {}
        try:
            r = session.get(f"{JENKINS_URL}/crumbIssuer/api/json", auth=HTTPBasicAuth(JENKINS_USER, initial_token), timeout=10)
            if r.status_code == 200:
                cj = r.json()
                headers = {cj.get("crumbRequestField"): cj.get("crumb")}
        except Exception:
            pass

        token_name = "initial-token"
        post_url = f"{JENKINS_URL}/user/{JENKINS_USER}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken"
        r = session.post(post_url, auth=HTTPBasicAuth(JENKINS_USER, initial_token), headers=headers, data={"newTokenName": token_name}, timeout=10)
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        # Attempt common locations for token value in response
        token = None
        if isinstance(data, dict):
            token = data.get("data", {}).get("tokenValue") or data.get("tokenValue")
        # Fallback: try to locate token in response text
        if not token and r.text:
            import re
            m = re.search(r"tokenValue\"\s*:\s*\"(?P<t>[0-9a-fA-F-]+)\"", r.text)
            if m:
                token = m.group("t")
        if not token:
            print("✗ Could not generate API token (unexpected response)")
            return None
        # Write to env file (mounted)
        try:
            with open(JENKINS_ENV_FILE, "w") as f:
                f.write(f"JENKINS_USER={JENKINS_USER}\n")
                f.write(f"JENKINS_TOKEN={token}\n")
            print(f"✓ Wrote Jenkins token to {JENKINS_ENV_FILE}")
        except Exception as e:
            print(f"✗ Failed to write env file: {e}")
            return None
        return token
    except Exception as e:
        print(f"✗ Error generating token: {e}")
        return None

# Set session.auth later after token is determined
session.auth = None

jobs = [
    {
        "name": "API-Health-Check",
        "description": "Check health of critical APIs",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Check health of critical APIs</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Health Check") {
            steps {
                sh "echo Checking API health..."
                sh "curl -I https://www.google.com || true"
                sh "curl -I https://api.github.com || true"
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    },
    {
        "name": "Yahoo-Stock-Scraper",
        "description": "Fetch stock prices from Yahoo Finance",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Fetch stock prices from Yahoo Finance</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Fetch Stock") {
            steps {
                sh "echo Fetching stock data for AAPL..."
                sh "python3 -c \\"import yfinance as yf; stock = yf.Ticker('AAPL'); print(stock.info['currentPrice'])\\""
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    },
    {
        "name": "Git-Repository-Clone",
        "description": "Clone a git repository",
        "xml": '''<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.job.WorkflowJob plugin="workflow-job@1319.v7eb_51b_2a_fa_61">
  <actions/>
  <description>Clone a git repository</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3809.v6ad307f7d7a_7">
    <script>pipeline {
    agent any
    stages {
        stage("Clone") {
            steps {
                echo "Clone Repository Stage"
                sh "echo Configure this job with a git repository URL"
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</org.jenkinsci.plugins.workflow.job.WorkflowJob>'''
    }
]

def wait_for_jenkins(timeout=300):
    """Wait for Jenkins to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = session.get(f"{JENKINS_URL}/api/json")
            if r.status_code == 200:
                print("✓ Jenkins is ready")
                return True
        except:
            pass
        time.sleep(5)
    print("✗ Jenkins did not start within timeout")
    return False

def create_job(name, xml):
    """Create a job via Jenkins API"""
    try:
        r = session.get(f"{JENKINS_URL}/job/{name}/api/json")
        if r.status_code == 200:
            print(f"✓ Job already exists: {name}")
            return True
    except:
        pass
    
    try:
        r = session.post(
            f"{JENKINS_URL}/createItem",
            params={"name": name},
            data=xml,
            headers={"Content-Type": "application/xml"}
        )
        if r.status_code == 201:
            print(f"✓ Created job: {name}")
            return True
        else:
            print(f"✗ Failed to create {name}: {r.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error creating {name}: {e}")
        return False

if __name__ == "__main__":
    print(f"Jenkins URL: {JENKINS_URL}")
    print(f"Waiting for Jenkins to be ready...")
    
    if not wait_for_jenkins():
        sys.exit(1)
    
    print("\nCreating pipeline jobs...")
    for job in jobs:
        create_job(job["name"], job["xml"])
    
    print("\n✓ Job initialization complete")
