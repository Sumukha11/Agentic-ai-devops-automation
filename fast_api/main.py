from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jenkins_client import (
    list_jobs,
    trigger_build,
    get_status,
    get_last_status,
    get_logs,
)

app = FastAPI(
    title="Jenkins Automation API",
    description="FastAPI wrapper for Jenkins CI/CD",
    version="2.0"
)


# -------------------------------
# REQUEST MODEL
# -------------------------------
class BuildRequest(BaseModel):
    job_name: str


# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.get("/")
def root():
    return {
        "message": "FastAPI Jenkins Wrapper Running",
        "status": "OK"
    }


# -------------------------------
# GET ALL JOBS
# -------------------------------
@app.get("/jobs")
def get_jobs():
    result = list_jobs()

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {
        "success": True,
        "jobs": result,
        "count": len(result)
    }


# -------------------------------
# TRIGGER BUILD
# -------------------------------
@app.post("/build")
def build_job(request: BuildRequest):
    result = trigger_build(request.job_name)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {
        "success": True,
        **result
    }


# -------------------------------
# GET LAST BUILD STATUS
# -------------------------------
@app.get("/status/{job_name}/last")
def job_status_last(job_name: str):
    result = get_last_status(job_name)

    if isinstance(result, dict) and "error" in result:
        err = result["error"]

        # Handle "no builds yet"
        if "404" in str(err) or "Not Found" in str(err):
            return {
                "success": True,
                "job": job_name,
                "build_number": None,
                "status": None
            }

        raise HTTPException(status_code=500, detail=result)

    return {
        "success": True,
        **result
    }


# -------------------------------
# GET SPECIFIC BUILD STATUS
# -------------------------------
@app.get("/status/{job_name}/{build_number}")
def job_status_build(job_name: str, build_number: int):
    result = get_status(job_name, build_number)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result)

    # Normalize RUNNING state
    if result.get("status") is None:
        result["status"] = "RUNNING"

    return {
        "success": True,
        **result
    }


# -------------------------------
# BACKWARD COMPATIBILITY ROUTE
# -------------------------------
@app.get("/status/{job_name}")
def job_status(job_name: str):
    result = get_last_status(job_name)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {
        "success": True,
        **result
    }


# -------------------------------
# GET BUILD LOGS
# -------------------------------
@app.get("/logs/{job_name}/{build_number}")
def job_logs(job_name: str, build_number: int):
    result = get_logs(job_name, build_number)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result)

    logs_value = result.get("logs") or result.get("message") or ""

    return {
        "success": True,
        "job": job_name,
        "build_number": build_number,
        "logs": logs_value
    }