import os
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

ENV_PATH = "/workspace/.env"

# 🔥 WAIT FOR ENV FILE
def load_env():
    for _ in range(30):
        if os.path.exists(ENV_PATH):
            load_dotenv(ENV_PATH)
            return
        time.sleep(2)
    raise Exception(".env not found. Jenkins init may have failed.")

load_env()

JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

def get_auth():
    return HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)


def safe_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=30, **kwargs)

        if response.status_code >= 400:
            return None, {
                "error": f"{response.status_code} Error",
                "details": response.text[:300]
            }

        return response, None

    except Exception as e:
        return None, {"error": str(e)}


def list_jobs():
    url = f"{JENKINS_URL}/api/json"

    response, error = safe_request("GET", url, auth=get_auth())
    if error:
        return error

    try:
        jobs = response.json().get("jobs", [])
        return [job["name"] for job in jobs]
    except Exception as e:
        return {"error": str(e)}


def get_crumb():
    url = f"{JENKINS_URL}/crumbIssuer/api/json"

    response, error = safe_request("GET", url, auth=get_auth())
    if error:
        return None, error

    try:
        data = response.json()
        return data, None
    except Exception as e:
        return None, {"error": str(e)}


def trigger_build(job_name):
    try:
        crumb_data, error = get_crumb()
        if error:
            return error

        headers = {
            crumb_data["crumbRequestField"]: crumb_data["crumb"]
        }

        url = f"{JENKINS_URL}/job/{job_name}/build"

        response, error = safe_request(
            "POST",
            url,
            auth=get_auth(),
            headers=headers,
            allow_redirects=False
        )

        if error:
            return error

        queue_url = response.headers.get("Location")

        if not queue_url:
            return {"error": "Queue location not found from Jenkins"}

        for _ in range(20):
            time.sleep(3)

            q_res, q_err = safe_request(
                "GET",
                f"{queue_url}api/json",
                auth=get_auth()
            )

            if q_err:
                continue

            q_data = q_res.json()

            if "executable" in q_data:
                return {
                    "status": "TRIGGERED",
                    "job": job_name,
                    "build_number": q_data["executable"]["number"]
                }

        return {"error": "Timeout waiting for build to start"}

    except Exception as e:
        return {"error": str(e)}


def get_status(job_name, build_number):
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/api/json"

    response, error = safe_request("GET", url, auth=get_auth())
    if error:
        return error

    try:
        data = response.json()
        return {
            "job": job_name,
            "build_number": build_number,
            "status": data.get("result") or "RUNNING",
            "building": data.get("building", False),
            "duration": data.get("duration", 0)
        }
    except Exception as e:
        return {"error": str(e)}


def get_last_status(job_name):
    url = f"{JENKINS_URL}/job/{job_name}/lastBuild/api/json"

    response, error = safe_request("GET", url, auth=get_auth())
    if error:
        return {"job": job_name, "build_number": None, "status": None}

    try:
        data = response.json()
        return {
            "job": job_name,
            "build_number": data.get("number"),
            "status": data.get("result")
        }
    except Exception as e:
        return {"error": str(e)}


def get_logs(job_name, build_number):
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/consoleText"

    for _ in range(5):
        response, error = safe_request("GET", url, auth=get_auth())

        if error:
            time.sleep(2)
            continue

        logs = response.text
        if logs.strip():
            return {"job": job_name, "build_number": build_number, "logs": logs}

        time.sleep(2)

    return {"message": "Logs not available yet"}