import requests
import os
import json
import time
import traceback
import difflib
import re
from langchain_ollama import OllamaLLM

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

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
            test_llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3")
            llm = test_llm
            print("✅ LLM client initialized (Ollama - llama3).")
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
            "model": "llama3",
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False
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
        
        valid_tools = ["list_jobs", "trigger_build", "get_status", "get_logs", "chat"]
        if tool not in valid_tools:
            print(f"⚠️ Invalid tool name: {tool}")
            return {"tool": "chat", "arguments": {"message": f"Unknown tool: {tool}. I only support triggering one job at a time."}}
        
        print(f"✅ Valid tool: {tool}")
        return parsed
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Response: {response[:200]}")
        return {"tool": "chat", "arguments": {"message": "I couldn't process that. Could you rephrase?"}}


def find_best_job_match(user_input, available_jobs):
    """Find closest matching job name."""
    if not available_jobs:
        return None

    normalized_input = re.sub(r"[^a-zA-Z0-9]", "", user_input).lower()
    normalized_jobs = {
        re.sub(r"[^a-zA-Z0-9]", "", job).lower(): job
        for job in available_jobs
    }

    matches = difflib.get_close_matches(normalized_input, normalized_jobs.keys(), n=1, cutoff=0.4)
    return normalized_jobs[matches[0]] if matches else None


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
            timeout=10
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
   - "get_status" (check status with "job_name")
   - "get_logs" (get logs with "job_name" and "build_number")
   - "chat" (conversational response with "message")

4. ARGUMENT RULES:
   - trigger_build: {"job_name": "NAME", "parameters": {"KEY": "VALUE"}} - STRING and optional map
   - get_status: {"job_name": "NAME"}
   - list_jobs: {}
   - chat: {"message": "TEXT"}

5. MULTI-JOB DETECTION:
   - Single job only. Do not use batch actions.

═════════════════════════════════════════════════════════════════════════════════

EXAMPLES (output EXACTLY like this):

- "list jobs" → {"tool": "list_jobs", "arguments": {}}
- "run health check" → {"tool": "trigger_build", "arguments": {"job_name": "API-Health-Check"}}
- "run git clone" → {"tool": "trigger_build", "arguments": {"job_name": "Git-Repository-Clone", "parameters": {"GIT_REPO_URL": "https://github.com/githubtraining/hellogitworld.git"}}}
- "hi" → {"tool": "chat", "arguments": {"message": "Hello! I can list jobs, trigger a single build, or check status. What would you like?"}}
- "unclear input" → {"tool": "chat", "arguments": {"message": "I didn't understand. Could you clarify?"}}

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
            response = {
                "message": "Here are the available Jenkins jobs.",
                "jobs": jobs_result.get("jobs", [])
            }

        # TRIGGER SINGLE BUILD
        elif tool_name == "trigger_build":
            jobs_result = list_jenkins_jobs()
            available_jobs = jobs_result.get("jobs", [])
            requested_job = args.get("job_name", "").strip()
            parameters = args.get("parameters") if isinstance(args.get("parameters"), dict) else None
            matched_job = find_best_job_match(requested_job, available_jobs)

            if not requested_job:
                response = {
                    "message": "Please specify the job name to trigger. Optionally include parameters as {'parameters': {'KEY': 'VALUE'}}."
                }
            elif not matched_job:
                response = {
                    "message": f"Could not find job matching '{requested_job}'. Available: {available_jobs}",
                    "available_jobs": available_jobs
                }
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
                        "message": "✅ Build triggered!",
                        "job": matched_job,
                        "build_number": build_number,
                        "status": build_result.get("status", "TRIGGERED"),
                        "parameters": parameters,
                        "info": f"Build #{build_number} queued. Use 'check status {matched_job}' to monitor."
                    }

        # GET STATUS
        elif tool_name == "get_status":
            requested_job = args.get("job_name", "").strip()
            build_number = args.get("build_number", None)

            if not requested_job:
                response = {
                    "message": "Please provide a job name for the status check."
                }
            else:
                try:
                    if build_number:
                        status_result = requests.get(
                            f"{FASTAPI_URL}/status/{requested_job}/{build_number}",
                            timeout=10
                        ).json()
                    else:
                        status_result = requests.get(
                            f"{FASTAPI_URL}/status/{requested_job}/last",
                            timeout=10
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
            response = {
                "message": args.get("message", "Hello! I'm Lamma, your DevOps assistant. How can I help?")
            }

        return {"success": True, "response": response}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}
