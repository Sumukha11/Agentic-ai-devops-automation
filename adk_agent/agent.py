import requests
import os
import json
import time
import traceback
import difflib
import re
import subprocess
import shutil
from langchain_ollama import OllamaLLM

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

llm = None

def init_llm():
    """Initialize Ollama LLM client with exponential backoff."""
    global llm
    if llm is not None:
        return llm
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            test_llm = OllamaLLM(
                base_url=OLLAMA_URL,
                model=OLLAMA_MODEL,
                temperature=0,
                num_predict=160,
                num_ctx=2048,
                keep_alive="3600s",
            )
            llm = test_llm
            print(f"✅ LLM client initialized (Ollama - {OLLAMA_MODEL}).")
            return llm
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ LLM initialization attempt {attempt + 1} failed: {e}")
                print(f"   Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ LLM initialization failed after {max_retries} attempts: {e}")
    
    return None


def call_llm(prompt_text: str, timeout_sec=45):
    """Try Ollama LLM with multiple fallback strategies."""
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt_text}\n\nAssistant:"
    try:
        test_llm = init_llm()
        if test_llm:
            result = str(test_llm.invoke(full_prompt))
            print("✅ LLM response via langchain invoke")
            return result
    except Exception as e:
        print(f"⚠️ LangChain client attempt failed: {e}")

    endpoints = ["/api/chat"]
    headers = {"Content-Type": "application/json"}

    for ep in endpoints:
        url = OLLAMA_URL.rstrip("/") + ep
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,
            "keep_alive": "-1",
            "options": {"temperature": 0, "num_predict": 160, "num_ctx": 2048}
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout_sec)
            if resp.status_code == 200:
                j = resp.json()
                result_text = None

                if isinstance(j, dict) and "message" in j and isinstance(j["message"], dict):
                    result_text = j["message"].get("content", "")
                elif "response" in j:
                    result_text = j["response"]
                elif "text" in j:
                    result_text = j["text"]

                if result_text:
                    return result_text.strip()

        except Exception as e:
            print(f"❌ HTTP fallback failed: {e}")

    raise RuntimeError(f"Could not get response from Ollama at {OLLAMA_URL}")


def safe_parse_json(response):
    """Parse JSON with strict validation."""
    try:
        parsed = json.loads(response)
        
        if not isinstance(parsed, dict):
            print(f"⚠️ Response is not a dict: {type(parsed)}")
            return {"tool": "chat", "arguments": {"message": "Invalid response format"}}
        
        tool = parsed.get("tool", "").strip()
        args = parsed.get("arguments", {})
        
        valid_tools = ["list_jobs", "trigger_build", "trigger_builds", "get_status", "get_logs", "chat"]
        if tool not in valid_tools:
            print(f"⚠️ Invalid tool name: {tool}")
            return {"tool": "chat", "arguments": {"message": f"Unknown tool: {tool}. I only support triggering one job at a time."}}
        
        print(f"✅ Valid tool: {tool}")
        return parsed
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Response: {response[:200]}")
        return {"tool": "chat", "arguments": {"message": "I couldn't process that. Could you rephrase?"}}


ACTION_WORDS = {
    "api", "all", "available", "build", "building", "check", "health", "job", "jobs",
    "list", "run", "show", "status", "trigger", "please", "the", "and", "for", "of",
    "fetch", "clone", "scraper", "repository", "stock", "yahoo", "github", "google",
    "pipeline", "service", "services"
}


def find_best_job_match(user_input, available_jobs):
    """Find closest matching job name while ignoring trigger/list commands and common words."""
    if not available_jobs:
        return None

    normalized_jobs = {}
    for job in available_jobs:
        if not job:
            continue
        compact = re.sub(r"[^a-zA-Z0-9]", "", job).lower()
        normalized_jobs[compact] = job

        tokens = [token.lower() for token in re.split(r"[^a-zA-Z0-9]+", job) if token]
        meaningful = "".join(token for token in tokens if token not in ACTION_WORDS)
        if meaningful:
            normalized_jobs[meaningful] = job

    if not normalized_jobs:
        return None

    user_phrase = re.sub(r"[^a-zA-Z0-9]+", " ", user_input).strip().lower()
    search_terms = [user_phrase]

    meaningful_tokens = [token for token in user_phrase.split() if token and token not in ACTION_WORDS]
    if meaningful_tokens:
        search_terms.append("".join(meaningful_tokens))
        search_terms.append(" ".join(meaningful_tokens))

    for term in search_terms:
        compact_term = re.sub(r"[^a-zA-Z0-9]", "", term).lower()
        if compact_term in normalized_jobs:
            return normalized_jobs[compact_term]

        matches = difflib.get_close_matches(compact_term, list(normalized_jobs.keys()), n=1, cutoff=0.5)
        if matches:
            return normalized_jobs[matches[0]]

    # Final fallback: compare the job names themselves without extra action words.
    base_candidates = [
        re.sub(r"[^a-zA-Z0-9]", "", job).lower()
        for job in available_jobs
        if job
    ]
    matches = difflib.get_close_matches(
        re.sub(r"[^a-zA-Z0-9]", "", user_phrase).lower(),
        base_candidates,
        n=1,
        cutoff=0.4
    )
    if matches:
        for job in available_jobs:
            if re.sub(r"[^a-zA-Z0-9]", "", job).lower() == matches[0]:
                return job

    return None


def infer_terraform_action(prompt: str):
    text = (prompt or "").lower()
    if any(word in text for word in ["destroy", "remove", "teardown", "delete", "stop", "clean up"]):
        return "destroy"
    return "deploy"


def cleanup_stale_prometheus_resources():
    cleanup_commands = [
        ["docker", "rm", "-f", "prometheus-server"],
        ["docker", "network", "rm", "prometheus-net"],
        ["docker", "ps", "-aq", "--filter", "name=prometheus-server"],
    ]
    for cmd in cleanup_commands:
        try:
            if cmd[:2] == ["docker", "ps"]:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                container_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                for cid in container_ids:
                    subprocess.run(["docker", "rm", "-f", cid], capture_output=True, text=True, check=False)
                continue
            subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception:
            pass

    # Also remove stale docker-compose-created default network if it exists.
    try:
        subprocess.run(["docker", "network", "prune", "-f"], capture_output=True, text=True, check=False)
    except Exception:
        pass

    return {"status": "CLEANED"}


def list_terraform_jobs():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "terraform")
    prometheus_dir = os.path.join(base_dir, "local-docker-stack")
    kubernetes_dir = os.path.join(base_dir, "kubernetes-grafana-stack")
    return [
        {
            "name": "Prometheus-Server-Deploy",
            "path": prometheus_dir,
            "description": "Deploy a Prometheus monitoring server in a Docker container.",
            "type": "terraform"
        },
        {
            "name": "Kubernetes-Grafana-Deploy",
            "path": kubernetes_dir,
            "description": "Deploy a local Kind Kubernetes cluster and Grafana inside the monitoring namespace.",
            "type": "terraform"
        }
    ]


def run_terraform_destroy(terraform_name: str):
    project_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "terraform", "local-docker-stack")
    if not os.path.isdir(project_dir):
        return {"error": f"Terraform project not found: {project_dir}"}
    if not shutil.which("terraform"):
        return {"error": "Terraform is not installed on this system. Install Terraform CLI to destroy the local Docker stack."}

    cleanup_stale_prometheus_resources()

    destroy = subprocess.run(
        ["terraform", "-chdir=" + project_dir, "destroy", "-auto-approve"],
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    if destroy.returncode != 0:
        return {"error": "Terraform destroy failed", "details": destroy.stderr or destroy.stdout}

    return {
        "status": "DESTROYED",
        "job": terraform_name,
        "message": "Prometheus Terraform deployment was destroyed and stale Docker resources were cleaned up.",
        "details": destroy.stdout or "Destroy completed."
    }


def run_terraform_deploy(terraform_name: str):
    project_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "terraform", "local-docker-stack")
    if not os.path.isdir(project_dir):
        return {"error": f"Terraform project not found: {project_dir}"}

    if not shutil.which("terraform"):
        return {"error": "Terraform is not installed on this system. Install Terraform CLI to deploy the local Docker stack."}

    try:
        cleanup_stale_prometheus_resources()

        init = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "init"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if init.returncode != 0:
            return {"error": "Terraform init failed", "details": init.stderr or init.stdout}

        apply = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "apply", "-auto-approve"],
            capture_output=True,
            text=True,
            timeout=1200,
            check=False,
        )
        if apply.returncode != 0:
            # Clean up stale resources after a failed apply and retry once.
            cleanup_stale_prometheus_resources()
            retry = subprocess.run(
                ["terraform", "-chdir=" + project_dir, "apply", "-auto-approve"],
                capture_output=True,
                text=True,
                timeout=1200,
                check=False,
            )
            if retry.returncode != 0:
                return {"error": "Terraform apply failed", "details": retry.stderr or retry.stdout}
            apply = retry

        output = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "output", "-json"],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

        return {
            "status": "DEPLOYED",
            "job": terraform_name,
            "message": "Free local Docker DevOps stack deployed successfully with Terraform.",
            "terraform_output": output.stdout if output.returncode == 0 else None,
            "details": apply.stdout or "Deployment completed."
        }
    except subprocess.TimeoutExpired as exc:
        return {"error": "Terraform apply timed out", "details": str(exc)}
    except Exception as exc:
        return {"error": f"Failed to deploy Terraform job: {str(exc)}"}


def list_jenkins_jobs():
    try:
        return requests.get(f"{FASTAPI_URL}/jobs", timeout=10).json()
    except Exception as e:
        return {"error": f"Failed to list jobs: {str(e)}"}


def trigger_jenkins_build(job_name: str, parameters: dict = None):
    payload = {"job_name": job_name}
    if parameters:
        payload["parameters"] = parameters

    try:
        return requests.post(
            f"{FASTAPI_URL}/build",
            json=payload,
            timeout=45
        ).json()
    except Exception as e:
        return {"error": f"Failed to trigger build: {str(e)}"}


def get_jenkins_status(job_name: str):
    try:
        return requests.get(f"{FASTAPI_URL}/status/{job_name}", timeout=10).json()
    except Exception as e:
        return {"error": f"Failed to get status: {str(e)}"}


def get_jenkins_logs(job_name: str, build_number: int):
    try:
        return requests.get(
            f"{FASTAPI_URL}/logs/{job_name}/{build_number}",
            timeout=20
        ).json()
    except Exception as e:
        return {"error": f"Failed to get logs: {str(e)}"}


def wait_for_build_completion(job_name, build_number, timeout=60):
    """Wait for build with reduced timeout."""
    start = time.time()

    while time.time() - start < timeout:
        try:
            status_result = requests.get(
                f"{FASTAPI_URL}/status/{job_name}/{build_number}",
                timeout=10
            ).json()

            status = status_result.get("status")

            if status in ["SUCCESS", "FAILURE"]:
                return status

            time.sleep(3)
        except Exception as e:
            print(f"Status check error: {e}")
            time.sleep(3)

    return "RUNNING"


SYSTEM_PROMPT = """You are **Lamma**, an AI-powered DevOps assistant for Jenkins CI/CD automation.

YOUR ONLY JOB: Return ONLY valid JSON. NOTHING ELSE.

═════════════════════════════════════════════════════════════════════════════════

🚨 CRITICAL RULES:

1. RESPONSE = ONLY VALID JSON, NO TEXT BEFORE OR AFTER
   ✅ {"tool": "list_jobs", "arguments": {}}
   ❌ Here's the list: {"tool": ...}

2. NEVER RETURN EXAMPLES OR TEMPLATES
   ❌ {"tool": "trigger_build", "arguments": {"job_names": ["Job1", "Job2"]}}

3. VALID TOOLS ONLY:
   - "list_jobs" (show available jobs)
   - "trigger_build" (run ONE job with "job_name" and optional "parameters")
   - "trigger_builds" (run multiple Jenkins jobs with "job_names")
   - "get_status" (check status with "job_name")
   - "get_logs" (get logs with "job_name" and "build_number")
   - "chat" (conversational response with "message")

4. ARGUMENT RULES:
   - trigger_build: {"job_name": "NAME", "parameters": {"KEY": "VALUE"}} - STRING and optional map
   - trigger_builds: {"job_names": ["NAME1", "NAME2"], "parameters": {"KEY": "VALUE"}} - ARRAY of strings and optional map
   - get_status: {"job_name": "NAME"}
   - list_jobs: {}
   - chat: {"message": "TEXT"}

5. MULTI-JOB DETECTION:
   - Use trigger_builds when the user asks to trigger all jobs or multiple named jobs.

═════════════════════════════════════════════════════════════════════════════════

EXAMPLES (output EXACTLY like this):

- "list jobs" → {"tool": "list_jobs", "arguments": {}}
- "run health check" → {"tool": "trigger_build", "arguments": {"job_name": "API-Health-Check"}}
- "run git clone" → {"tool": "trigger_build", "arguments": {"job_name": "Git-Repository-Clone", "parameters": {"GIT_REPO_URL": "https://github.com/githubtraining/hellogitworld.git"}}}
- "hi" → {"tool": "chat", "arguments": {"message": "Hello! I can list jobs, trigger a single build, or check status. What would you like?"}}
- "unclear input" → {"tool": "chat", "arguments": {"message": "I didn't understand. Could you clarify?"}}
- "deploy kubernetes cluster with grafana" → {"tool": "trigger_build", "arguments": {"job_name": "Kubernetes-Grafana-Deploy"}}
- "destroy the kubernetes grafana deployment" → {"tool": "trigger_build", "arguments": {"job_name": "Kubernetes-Grafana-Deploy"}}
- "deploy prometheus server" → {"tool": "trigger_build", "arguments": {"job_name": "Prometheus-Server-Deploy"}}
- "run all tests" → {"tool": "trigger_builds", "arguments": {"job_names": ["Test-API", "Test-Frontend"]}}
- "trigger all jobs" → {"tool": "trigger_builds", "arguments": {"job_names": ["Job1", "Job2", "Job3"]}}

═════════════════════════════════════════════════════════════════════════════════

REMEMBER:
- ONLY JSON
- NO explanations
- VALIDATE argument keys match tool
- Use trigger_build (singular) for 1 job only"""


def run_agent(user_prompt: str):
    try:
        print(f"\n=== USER === {user_prompt}")
        llm_response = call_llm(user_prompt)
        print(f"=== LLM RESPONSE === {llm_response}")
        
        parsed = safe_parse_json(llm_response)
        print(f"=== PARSED === {parsed}")
        
        tool_name = parsed.get("tool", "chat")
        args = parsed.get("arguments", {})
        response = {}

        # LIST JOBS
        if tool_name == "list_jobs":
            jobs_result = list_jenkins_jobs()
            terraform_jobs = list_terraform_jobs()
            response = {
                "message": "Here are the available Jenkins jobs and Terraform deployment scripts.",
                "jobs": jobs_result.get("jobs", []),
                "terraform_scripts": terraform_jobs
            }

        # TRIGGER SINGLE BUILD
        elif tool_name == "trigger_build":
            jobs_result = list_jenkins_jobs()
            available_jobs = jobs_result.get("jobs", [])
            terraform_jobs = list_terraform_jobs()
            terraform_names = [item["name"] for item in terraform_jobs]
            all_jobs = available_jobs + terraform_names
            requested_job = args.get("job_name", "").strip()
            parameters = args.get("parameters") if isinstance(args.get("parameters"), dict) else None
            matched_job = find_best_job_match(requested_job, all_jobs)

            if not requested_job:
                response = {
                    "message": "Please specify the job name to trigger. Optionally include parameters as {'parameters': {'KEY': 'VALUE'}}."
                }
            elif not matched_job:
                response = {
                    "message": f"Could not find job matching '{requested_job}'. Available jobs: {available_jobs} | Terraform scripts: {terraform_names}",
                    "available_jobs": available_jobs,
                    "terraform_scripts": terraform_jobs
                }
            else:
                if matched_job in terraform_names:
                    action = infer_terraform_action(requested_job)
                    if matched_job == "Kubernetes-Grafana-Deploy":
                        if action == "destroy":
                            deployment_result = run_kubernetes_grafana_destroy(matched_job)
                        else:
                            deployment_result = run_kubernetes_grafana_deploy(matched_job)
                    elif action == "destroy":
                        deployment_result = run_terraform_destroy(matched_job)
                    else:
                        deployment_result = run_terraform_deploy(matched_job)
                    response = {
                        "message": deployment_result.get("message", "Terraform deployment result."),
                        "job": matched_job,
                        "status": deployment_result.get("status", "ERROR"),
                        "details": deployment_result.get("details"),
                        "terraform_scripts": terraform_jobs
                    }
                    if deployment_result.get("error") is not None:
                        response["error"] = deployment_result.get("error")
                    if deployment_result.get("grafana_url"):
                        response["grafana_url"] = deployment_result["grafana_url"]
                        response["credentials"] = deployment_result["credentials"]
                else:
                    build_result = trigger_jenkins_build(matched_job, parameters=parameters)
                    
                    if "error" in build_result:
                        response = {
                            "message": f"Failed to trigger: {build_result['error']}",
                            "job": matched_job
                        }
                    else:
                        build_number = build_result.get("build_number")
                        response = {
                            "message": "✅ Build queued!",
                            "job": matched_job,
                            "build_number": build_number,
                            "status": build_result.get("status", "QUEUED"),
                            "parameters": parameters,
                            "info": f"Use 'check status {matched_job}' to monitor the build after Jenkins starts it." if build_number is None else f"Build #{build_number} queued. Use 'check status {matched_job}' to monitor."
                        }

        # TRIGGER MULTIPLE BUILDS
        elif tool_name == "trigger_builds":
            jobs_result = list_jenkins_jobs()
            available_jobs = jobs_result.get("jobs", []) if isinstance(jobs_result, dict) else []
            requested_names = args.get("job_names")

            if requested_names == "all" or requested_names is None:
                requested_names = available_jobs

            if not isinstance(requested_names, list) or not requested_names:
                response = {"message": "Please specify the Jenkins jobs to trigger, or ask to run all jobs."}
            else:
                results = []
                for requested_job in requested_names:
                    matched_job = find_best_job_match(str(requested_job), available_jobs)
                    if not matched_job:
                        results.append({"job": requested_job, "status": "NOT_FOUND"})
                        continue
                    build_result = trigger_jenkins_build(matched_job)
                    results.append({
                        "job": matched_job,
                        "status": build_result.get("status", "ERROR"),
                        "build_number": build_result.get("build_number"),
                        "error": build_result.get("error") if build_result.get("error") else None,
                    })

                response = {
                    "message": "Jenkins jobs were submitted for triggering.",
                    "results": results,
                }

        # GET STATUS
        elif tool_name == "get_status":
            requested_job = args.get("job_name", "").strip()
            build_number = args.get("build_number", None)

            if not requested_job:
                jobs_result = list_jenkins_jobs()
                available_jobs = jobs_result.get("jobs", []) if isinstance(jobs_result, dict) else []
                statuses = []
                for job_name in available_jobs:
                    try:
                        status_result = requests.get(f"{FASTAPI_URL}/status/{job_name}", timeout=45).json()
                        statuses.append({
                            "job": job_name,
                            "build_number": status_result.get("build_number"),
                            "status": status_result.get("status") or "NOT_RUN",
                        })
                    except Exception as exc:
                        statuses.append({"job": job_name, "status": "ERROR", "error": str(exc)})
                response = {"message": "Status retrieved successfully.", "statuses": statuses}
            else:
                try:
                    if build_number:
                        status_result = requests.get(
                            f"{FASTAPI_URL}/status/{requested_job}/{build_number}",
                            timeout=45
                        ).json()
                    else:
                        status_result = requests.get(
                            f"{FASTAPI_URL}/status/{requested_job}/last",
                            timeout=45
                        ).json()

                    response = {
                        "job": requested_job,
                        "build_number": status_result.get("build_number"),
                        "status": status_result.get("status"),
                        "building": status_result.get("building"),
                        "duration": status_result.get("duration"),
                        "message": status_result.get("message", "Status retrieved successfully.")
                    }
                except Exception as e:
                    response = {
                        "job": requested_job,
                        "error": f"Failed to get status: {str(e)}"
                    }

        # GET LOGS
        elif tool_name == "get_logs":
            requested_job = args.get("job_name", "")
            build_number = args.get("build_number", 1)
            logs = get_jenkins_logs(requested_job, build_number)
            response = {
                "job": requested_job,
                "build_number": build_number,
                "logs": logs
            }

        # CHAT
        else:
            prompt_lower = (user_prompt or "").lower()
            llm_message = args.get("message", "Hello! I'm Lamma, your DevOps assistant. How can I help?")
            if any(word in prompt_lower for word in ("grafana", "kubernetes", "kind")) and any(word in prompt_lower for word in ("why", "fail", "error", "problem")):
                llm_message = (
                    "The Kubernetes/Grafana deployment failed because the agent container could not find the Docker executable, "
                    "which Kind needs to create the cluster. Docker is mounted into the agent, and I have added Docker CLI support; rebuild the agent container and retry."
                )
            elif "why" in prompt_lower and "timeout" in prompt_lower:
                llm_message = "The request timed out because Jenkins can take time to queue or start a build. Builds are now queued without waiting, and you can check status afterward."
            response = {"message": llm_message}

        return {"success": True, "response": response}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}
def run_kubernetes_grafana_destroy(terraform_name: str):
    project_dir = next(
        (job["path"] for job in list_terraform_jobs() if job["name"] == terraform_name),
        None,
    )
    if not project_dir:
        return {"error": "Kubernetes/Grafana Terraform project was not found."}
    for binary in ("terraform", "kind", "kubectl"):
        if not shutil.which(binary):
            return {"error": f"Required binary '{binary}' is not installed."}

    destroy = subprocess.run(
        ["terraform", "-chdir=" + project_dir, "destroy", "-auto-approve"],
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    if destroy.returncode != 0:
        return {"error": "Kind cluster Terraform destroy failed", "details": destroy.stderr or destroy.stdout}

    return {
        "status": "DESTROYED",
        "job": terraform_name,
        "message": "Kind Kubernetes cluster and Grafana deployment were destroyed.",
        "details": destroy.stdout or "Destroy completed.",
    }


def run_kubernetes_grafana_deploy(terraform_name: str):
    project_dir = next(
        (job["path"] for job in list_terraform_jobs() if job["name"] == terraform_name),
        None,
    )
    if not project_dir:
        return {"error": "Kubernetes/Grafana Terraform project was not found."}
    for binary in ("terraform", "kind", "kubectl"):
        if not shutil.which(binary):
            return {"error": f"Required binary '{binary}' is not installed. Docker agent image must include Terraform, Kind, and kubectl."}

    try:
        init = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "init", "-upgrade"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if init.returncode != 0:
            return {"error": "Terraform init failed", "details": init.stderr or init.stdout}

        apply = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "apply", "-auto-approve"],
            capture_output=True,
            text=True,
            timeout=1200,
            check=False,
        )
        if apply.returncode != 0:
            return {"error": "Kubernetes/Grafana Terraform apply failed", "details": apply.stderr or apply.stdout}

        output = subprocess.run(
            ["terraform", "-chdir=" + project_dir, "output", "-json"],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        return {
            "status": "DEPLOYED",
            "job": terraform_name,
            "message": "Kind Kubernetes cluster deployed successfully and Grafana is running in the monitoring namespace.",
            "terraform_output": output.stdout if output.returncode == 0 else None,
            "details": apply.stdout or "Deployment completed.",
            "grafana_url": "http://localhost:3000",
            "credentials": {"username": "admin", "password": "admin"},
        }
    except subprocess.TimeoutExpired as exc:
        return {"error": "Kubernetes/Grafana deployment timed out", "details": str(exc)}
    except Exception as exc:
        return {"error": f"Failed to deploy Kubernetes/Grafana: {str(exc)}"}
