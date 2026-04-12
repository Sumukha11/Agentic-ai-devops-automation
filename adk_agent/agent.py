import requests
import os
import json
from langchain_ollama import OllamaLLM

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

# 🔥 LLM - Initialize but don't fail if model not available
llm = None
try:
    llm = OllamaLLM(
        base_url=OLLAMA_URL,
        model="mistral"
    )
    print("✅ LLM client initialized (Ollama).")
except Exception as e:
    print(f"⚠️ Warning: LLM initialization skipped: {e}")

# 🔧 TOOL IMPLEMENTATIONS
def list_jenkins_jobs():
    """List all available Jenkins jobs"""
    try:
        return requests.get(f"{FASTAPI_URL}/jobs", timeout=15).json()
    except Exception as e:
        return {"error": f"Failed to list jobs: {str(e)}"}


def trigger_jenkins_build(job_name: str):
    """Trigger Jenkins build"""
    try:
        return requests.post(
            f"{FASTAPI_URL}/build",
            json={"job_name": job_name},
            timeout=15
        ).json()
    except Exception as e:
        return {"error": f"Failed to trigger build: {str(e)}"}


def get_jenkins_status(job_name: str):
    """Get latest status of a Jenkins job"""
    try:
        return requests.get(
            f"{FASTAPI_URL}/status/{job_name}",
            timeout=15
        ).json()
    except Exception as e:
        return {"error": f"Failed to get status: {str(e)}"}


def get_jenkins_logs(job_name: str, build_number: int):
    """Get logs of a Jenkins job build"""
    try:
        return requests.get(
            f"{FASTAPI_URL}/logs/{job_name}/{build_number}",
            timeout=15
        ).json()
    except Exception as e:
        return {"error": f"Failed to get logs: {str(e)}"}


# 🎯 SYSTEM PROMPT
SYSTEM_PROMPT = """You are an AI DevOps assistant for Jenkins CI/CD automation.

You have access to the following capabilities:
- List all available Jenkins jobs
- Trigger builds for specific jobs
- Check the latest status of jobs
- View build logs

When users ask you to perform actions, use these capabilities to help them.
For list requests, respond with the list of jobs.
For build triggers, respond with confirmation and build number.
For status checks, respond with the current status.

Be helpful, conversational, and provide clear explanations."""

# 🚀 RUN AGENT - Simple, direct implementation
def run_agent(user_prompt: str):
    try:
        print(f"\n=== USER === {user_prompt}")

        # Check what the user wants to do
        prompt_lower = user_prompt.lower()
        
        # List jobs
        if "list" in prompt_lower or "show" in prompt_lower or "jobs" in prompt_lower:
            result = list_jenkins_jobs()
            if isinstance(result, dict) and "error" not in result and "jobs" in result:
                jobs = result.get("jobs", [])
                response = {"jobs": jobs}
            else:
                response = result if isinstance(result, dict) else {"error": str(result)}
        
        # Trigger build
        elif "trigger" in prompt_lower or "build" in prompt_lower or "run" in prompt_lower:
            # Try to extract job name from prompt (robust)
            import re
            words = user_prompt.split()
            job_name = None
            for i, word in enumerate(words):
                if word.lower() in ["trigger", "build", "run"] and i + 1 < len(words):
                    candidate = words[i + 1]
                    if candidate.lower() not in ["the", "a", "an", "please"]:
                        job_name = candidate
                        break

            def find_job_in_prompt(prompt_text: str):
                # Try to match known job names from Jenkins by token overlap
                try:
                    jr = list_jenkins_jobs()
                    jobs = []
                    if isinstance(jr, dict) and "jobs" in jr:
                        jobs = jr.get("jobs", [])
                    elif isinstance(jr, list):
                        jobs = jr
                    prompt_l = re.sub(r"[^a-z0-9 ]", " ", prompt_text.lower())
                    for j in jobs:
                        j_norm = re.sub(r"[^a-z0-9 ]", " ", j.lower())
                        # if all significant tokens of job appear in prompt, it's a match
                        j_tokens = [t for t in j_norm.split() if len(t) > 2]
                        if not j_tokens:
                            continue
                        matches = sum(1 for t in j_tokens if t in prompt_l)
                        if matches >= max(1, len(j_tokens)) or matches >= 1 and len(j_tokens) == 1:
                            return j
                except Exception:
                    pass
                # hardcoded synonyms
                if "health" in prompt_text.lower() or "api health" in prompt_text.lower():
                    return "API-Health-Check"
                return None

            if not job_name:
                inferred = find_job_in_prompt(user_prompt)
                if inferred:
                    job_name = inferred

            if not job_name:
                # If still no job name found, list jobs first
                jobs_result = list_jenkins_jobs()
                if isinstance(jobs_result, dict) and "jobs" in jobs_result:
                    jobs = jobs_result.get("jobs", [])
                    response = {"message": "Please specify which job to trigger.", "available_jobs": jobs}
                else:
                    response = {"error": "Could not list jobs. Please specify the job name."}
            else:
                result = trigger_jenkins_build(job_name)
                if isinstance(result, dict) and "error" not in result:
                    response = {"job": job_name, "build_number": result.get("build_number"), "status": result.get("status")}
                else:
                    response = result if isinstance(result, dict) else {"error": str(result)}
        
        # Get status
        elif "status" in prompt_lower or "check" in prompt_lower:
            words = user_prompt.split()
            job_name = None
            for i, word in enumerate(words):
                if word.lower() in ["status", "check"] and i + 1 < len(words):
                    job_name = words[i + 1]
                    break
            
            if not job_name:
                response = {"message": "Please specify which job to check status for."}
            else:
                result = get_jenkins_status(job_name)
                response = result if isinstance(result, dict) else {"error": str(result)}
        
        # Default: try LLM if available, otherwise guide user
        else:
            if llm:
                try:
                    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}\n\nAssistant:"
                    response_text = llm.invoke(full_prompt)
                    response = {"message": str(response_text)}
                    
                    # If LLM mentions listing jobs, include them
                    if "list" in str(response_text).lower() and "job" in str(response_text).lower():
                        jobs_result = list_jenkins_jobs()
                        if isinstance(jobs_result, dict) and "jobs" in jobs_result:
                            jobs = jobs_result.get("jobs", [])
                            response["available_jobs"] = jobs
                except Exception as e:
                    # Fallback if LLM call fails - don't show error to user
                    response = {
                        "message": "I can help you with Jenkins automation. Try commands like:\n- 'list jobs'\n- 'trigger build <job_name>'\n- 'check status <job_name>'"
                    }
            else:
                response = {
                    "message": "I can help you with Jenkins automation. Try commands like:\n- 'list jobs'\n- 'trigger build <job_name>'\n- 'check status <job_name>'"
                }

        print(f"=== RESPONSE === {response}")

        return {
            "response": response,
            "success": True
        }

    except Exception as e:
        error_msg = str(e)
        print(f"=== ERROR === {error_msg}")
        return {
            "error": error_msg,
            "success": False
        }