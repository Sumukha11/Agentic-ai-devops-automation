from fastapi import FastAPI
from pydantic import BaseModel
from adk_agent.agent import run_agent
from fast_api.jenkins_client import get_status, get_logs

app = FastAPI()


class Query(BaseModel):
    prompt: str


@app.post("/query")
def query(q: Query):
    print("\n=== REQUEST RECEIVED ===")
    print("Prompt:", q.prompt)

    response = run_agent(q.prompt)

    print("Response:", response)
    print("========================\n")

    # Return the agent payload directly (no double-wrapping)
    return response

@app.get("/status/{job}/{build}")
def status(job: str, build: int):
    return get_status(job, build)


@app.get("/logs/{job}/{build}")
def logs(job: str, build: int):
    return get_logs(job, build)