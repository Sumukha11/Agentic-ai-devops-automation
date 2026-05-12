import requests
import os
import json
import time
import traceback
import difflib
import re
from langchain_ollama import OllamaLLM

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://fastapi:8000"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434"
)

# 🔥 LLM - Lazy initialization (don't block container start)
llm = None

def init_llm():
    """
    Attempt to initialize the Ollama LLM client with exponential backoff.
    Safe to call repeatedly - caches successful initialization.
    """
    global llm
    if llm is not None:
        return llm  # Already initialized
    
    max_retries = 3
    base_delay = 2  # Start with 2 second delay
    
    for attempt in range(max_retries):
        try:
            test_llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3")
            llm = test_llm
            print("✅ LLM client initialized (Ollama - llama3).")
            return llm
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                print(f"⚠️ LLM initialization attempt {attempt + 1} failed: {e}")
                print(f"   Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ LLM initialization failed after {max_retries} attempts: {e}")
    
    return None


# Helper: robust LLM call that ALWAYS tries Ollama, with multiple fallbacks
def call_llm(prompt_text: str, timeout_sec=45):
    """
    Try Ollama LLM with multiple fallback strategies.
    Reduced timeout (45s) for responsive UI interactions.
    """
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt_text}\n\nAssistant:"
    try:
        test_llm = init_llm()
        if test_llm:
            result = str(test_llm.invoke(full_prompt))
            print("✅ LLM response via langchain invoke")
            return result
    except Exception as e:
        print(f"⚠️ LangChain client attempt failed: {e}")

    # Direct HTTP fallback
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

                # Standard formats
                if (
                    isinstance(j, dict)
                    and "message" in j
                    and isinstance(j["message"], dict)
                ):
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
    """
    Parse JSON response from LLM with strict validation.
    Logs issues for debugging.
    """
    try:
        parsed = json.loads(response)
        
        # Validate structure
        if not isinstance(parsed, dict):
            print(f"⚠️ Response is not a dict: {type(parsed)}")
            return {"tool": "chat", "arguments": {"message": "Invalid response format"}}
        
        tool = parsed.get("tool", "").strip()
        args = parsed.get("arguments", {})
        
        # Validate tool name
        valid_tools = ["list_jobs", "trigger_build", "trigger_builds", "get_status", "get_logs", "chat"]
        if tool not in valid_tools:
            print(f"⚠️ Invalid tool name: {tool}")
            return {"tool": "chat", "arguments": {"message": f"Unknown tool: {tool}"}}
        
        print(f"✅ Parsed valid JSON: tool={tool}, args={args}")
        return parsed
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Raw response: {response[:200]}")
        return {
            "tool": "chat",
            "arguments": {"message": "I couldn't process that. Could you rephrase?"}
        }
    except Exception as e:
        print(f"❌ Unexpected error in safe_parse_json: {e}")
        return {
            "tool": "chat",
            "arguments": {"message": "An error occurred processing your request"}
        }


def find_best_job_match(user_input, available_jobs):
    if not available_jobs:
        return None

    normalized_input = re.sub(r"[^a-zA-Z0-9]", "", user_input).lower()
    normalized_jobs = {
        re.sub(r"[^a-zA-Z0-9]", "", job).lower(): job
        for job in available_jobs
    }

    matches = difflib.get_close_matches(
        normalized_input,
        normalized_jobs.keys(),
        n=1,
        cutoff=0.4
    )
    return normalized_jobs[matches[0]] if matches else None


# 🔧 TOOL IMPLEMENTATIONS
def list_jenkins_jobs():
    try:
        return requests.get(f"{FASTAPI_URL}/jobs", timeout=10).json()
    except Exception as e:
        return {"error": f"Failed to list jobs: {str(e)}"}


def trigger_jenkins_build(job_name: str):
    try:
        return requests.post(
            f"{FASTAPI_URL}/build",
            json={"job_name": job_name},
            timeout=10
        ).json()
    except Exception as e:
        return {"error": f"Failed to trigger build: {str(e)}"}


def get_jenkins_status(job_name: str):
    try:
        return requests.get(
            f"{FASTAPI_URL}/status/{job_name}",
            timeout=10
        ).json()
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


# 🕒 WAIT FOR BUILD COMPLETION (with reduced timeout for UI responsiveness)
def wait_for_build_completion(job_name, build_number, timeout=60):
    """
    Wait for build completion with configurable timeout.
    Default 60s timeout prevents Streamlit UI from blocking.
    For longer builds, user can check status separately.
    """
    start = time.time()

    while time.time() - start < timeout:

        status_result = requests.get(
            f"{FASTAPI_URL}/status/{job_name}/{build_number}",
            timeout=10
        ).json()

        status = status_result.get("status")

        if status in ["SUCCESS", "FAILURE"]:
            return status

        time.sleep(3)

    return "RUNNING"  # Return RUNNING instead of TIMEOUT to indicate user can check later


# 🎯 SYSTEM PROMPT
SYSTEM_PROMPT = """
You are **Lamma**, an AI-powered DevOps assistant specializing in Jenkins CI/CD automation.

Your role is to help the user interact with a Jenkins environment by understanding natural language requests and responding with **ONLY valid JSON**, never text or markdown explanations.

Your behavior should simulate a helpful, concise, and intelligent DevOps chatbot that can:
- List Jenkins jobs
- Trigger one or multiple Jenkins builds
- Check the status of specific builds
- Retrieve and analyze Jenkins build logs
- Provide conversational replies (for greetings or clarifications)
- Always structure responses as JSON following the specified schema

---

### RESPONSE FORMAT

Respond **only** with valid JSON using the following format:

```json
{
  "tool": "<tool_name>",
  "arguments": {
      "key": "value"
  }
}

### Examples
User: list all Jenkins jobs
Response:
{
  "tool": "list_jobs",
  "arguments": {}
}

User: start the yahoo scraper job
Response:
{
  "tool": "trigger_build",
  "arguments": {
      "job_name": "Yahoo-Stock-Scraper"
  }
}

User: check if the fastapi deployment was successful
Response:
{
  "tool": "get_status",
  "arguments": {
      "job_name": "fastapi-deployment"
  }
}

User: hello there!
Response:
{
  "tool": "chat",
  "arguments": {
      "message": "Hello! I’m Lamma, your AI DevOps assistant for Jenkins automation. How can I help you today?"
  }
}

"""


# 🚀 RUN AGENT - Main entry
def run_agent(user_prompt: str):
    try:
        print(f"\n=== USER === {user_prompt}")
        llm_response = call_llm(user_prompt)
        parsed = safe_parse_json(llm_response)
        tool_name = parsed.get("tool", "chat")
        args = parsed.get("arguments", {})
        response = {}

        # STEP 2 — TOOL EXECUTION
        if tool_name == "list_jobs":
            jobs_result = list_jenkins_jobs()
            response = {
                "message": "Here are the available Jenkins jobs.",
                "jobs": jobs_result.get("jobs", [])
            }

        elif tool_name == "trigger_build":
            jobs_result = list_jenkins_jobs()
            available_jobs = jobs_result.get("jobs", [])
            requested_job = args.get("job_name", "")
            matched_job = find_best_job_match(requested_job, available_jobs)

            if not matched_job:
                response = {
                    "message": f"Could not find a matching Jenkins job for '{requested_job}'.",
                    "available_jobs": available_jobs
                }
            else:
                # 🚀 Trigger build and return immediately (async pattern)
                build_result = trigger_jenkins_build(matched_job)
                
                if "error" in build_result:
                    response = {
                        "message": f"Failed to trigger build: {build_result['error']}",
                        "job": matched_job
                    }
                else:
                    build_number = build_result.get("build_number")
                    response = {
                        "message": f"✅ Build triggered successfully!",
                        "job": matched_job,
                        "build_number": build_number,
                        "status": "QUEUED",
                        "info": f"Build #{build_number} has been queued. Use 'check status {matched_job}' to monitor progress."
                    }

        elif tool_name == "get_status":
            requested_job = args.get("job_name", "")
            build_number = args.get("build_number", None)
            
            try:
                if build_number:
                    # Get specific build status
                    status_result = requests.get(
                        f"{FASTAPI_URL}/status/{requested_job}/{build_number}",
                        timeout=10
                    ).json()
                else:
                    # Get last build status
                    status_result = requests.get(
                        f"{FASTAPI_URL}/status/{requested_job}/last",
                        timeout=10
                    ).json()
                
                response = {
                    "job": requested_job,
                    "build_info": status_result
                }
            except Exception as e:
                response = {
                    "job": requested_job,
                    "error": f"Failed to get status: {str(e)}"
                }

        elif tool_name == "get_logs":
            requested_job = args.get("job_name", "")
            build_number = args.get("build_number", 1)
            logs = get_jenkins_logs(requested_job, build_number)
            response = {
                "job": requested_job,
                "build_number": build_number,
                "logs": logs
            }

        else:
            response = {
                "message": args.get("message", "Hello! I'm Lamma, your AI DevOps assistant.")
            }

        return {"success": True, "response": response}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}
