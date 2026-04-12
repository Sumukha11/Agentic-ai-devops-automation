import requests
import os
import json
from langchain_ollama import OllamaLLM
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

llm = OllamaLLM(base_url=OLLAMA_URL, model="mistral")

@tool
def list_jenkins_jobs():
    """List all available Jenkins jobs"""
    try:
        res = requests.get(f"{FASTAPI_URL}/jobs", timeout=5)
        return res.json()
    except Exception as e:
        return {"error": f"Failed to list jobs: {str(e)}"}

@tool
def trigger_jenkins_build(job_name: str):
    """Trigger a Jenkins build for a specific job"""
    try:
        res = requests.post(
            f"{FASTAPI_URL}/build",
            json={"job_name": job_name},
            timeout=5
        )
        return res.json()
    except Exception as e:
        return {"error": f"Failed to trigger build: {str(e)}"}

@tool
def get_jenkins_status(job_name: str, build_number: int = None):
    """Get the status of a Jenkins job or specific build"""
    try:
        if build_number:
            res = requests.get(
                f"{FASTAPI_URL}/status/{job_name}/{build_number}",
                timeout=5
            )
        else:
            res = requests.get(
                f"{FASTAPI_URL}/status/{job_name}",
                timeout=5
            )
        return res.json()
    except Exception as e:
        return {"error": f"Failed to get status: {str(e)}"}

@tool
def get_jenkins_logs(job_name: str, build_number: int):
    """Get logs for a specific Jenkins build"""
    try:
        res = requests.get(
            f"{FASTAPI_URL}/logs/{job_name}/{build_number}",
            timeout=5
        )
        return res.json()
    except Exception as e:
        return {"error": f"Failed to get logs: {str(e)}"}

tools = [
    list_jenkins_jobs,
    trigger_jenkins_build,
    get_jenkins_status,
    get_jenkins_logs
]

agent = initialize_agent(
    tools,
    llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

system_prompt = """You are a Jenkins DevOps automation assistant. Your role is to help users manage Jenkins jobs and CI/CD pipelines.

You have access to the following capabilities:
- List available Jenkins jobs
- Trigger builds for Jenkins jobs
- Check job/build status
- View build logs

When a user asks you to do something:
1. First list available jobs if you don't know the specific job name
2. Match the user's intent to the appropriate action
3. Use the tools to perform the requested action
4. Return clear, actionable results

Always be helpful and provide context about what you're doing."""

def run_agent(user_prompt: str):
    """Run the agent with the user's prompt"""
    try:
        print(f"\n=== AGENT INPUT ===\nPrompt: {user_prompt}")
        
        full_prompt = f"{system_prompt}\n\nUser request: {user_prompt}"
        
        response = agent.run(full_prompt)
        
        print(f"Agent response: {response}")
        return {"response": response, "success": True}
    except Exception as e:
        error_msg = f"Agent error: {str(e)}"
        print(error_msg)
        return {"error": error_msg, "success": False}
