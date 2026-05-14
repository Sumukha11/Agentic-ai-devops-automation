from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jenkins_client import (
    list_jobs,
    trigger_build,
    get_status,
    get_last_status,
    get_logs,
)
from terraform_client import (
    terraform_init,
    terraform_plan,
    terraform_apply,
    terraform_destroy,
    terraform_output,
    terraform_state_show,
)

app = FastAPI(
    title="DevOps Automation API",
    description="FastAPI wrapper for Jenkins CI/CD and Terraform Infrastructure as Code",
    version="3.0"
)


# -------------------------------
# REQUEST MODEL
# -------------------------------
class BuildRequest(BaseModel):
    job_name: str
    parameters: Optional[Dict[str, str]] = None


class TerraformRequest(BaseModel):
    operation: str  # init, plan, apply, destroy
    var_file: Optional[str] = "terraform.tfvars"
    auto_approve: Optional[bool] = False


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
    result = trigger_build(request.job_name, parameters=request.parameters)

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


# ═══════════════════════════════════════════════════════════════
# TERRAFORM ENDPOINTS
# ═══════════════════════════════════════════════════════════════

# -------------------------------
# TERRAFORM INIT
# -------------------------------
@app.post("/terraform/init")
def tf_init():
    """Initialize Terraform working directory."""
    result = terraform_init()
    
    if result.get("status") != "SUCCESS":
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": True,
        "operation": "init",
        **result
    }


# -------------------------------
# TERRAFORM PLAN
# -------------------------------
@app.post("/terraform/plan")
def tf_plan(request: Optional[TerraformRequest] = None):
    """Generate and show an execution plan."""
    var_file = request.var_file if request else "terraform.tfvars"
    
    result = terraform_plan(var_file=var_file)
    
    if result.get("status") != "SUCCESS":
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": True,
        "operation": "plan",
        **result
    }


# -------------------------------
# TERRAFORM APPLY
# -------------------------------
@app.post("/terraform/apply")
def tf_apply(request: Optional[TerraformRequest] = None):
    """Apply Terraform configuration."""
    if not request:
        request = TerraformRequest(operation="apply")
    
    result = terraform_apply(
        auto_approve=request.auto_approve,
        var_file=request.var_file
    )
    
    if result.get("status") not in ["SUCCESS", "TIMEOUT"]:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": result.get("status") == "SUCCESS",
        "operation": "apply",
        **result
    }


# -------------------------------
# TERRAFORM DESTROY
# -------------------------------
@app.post("/terraform/destroy")
def tf_destroy(request: Optional[TerraformRequest] = None):
    """Destroy Terraform-managed infrastructure."""
    if not request:
        request = TerraformRequest(operation="destroy")
    
    result = terraform_destroy(
        auto_approve=request.auto_approve,
        var_file=request.var_file
    )
    
    if result.get("status") not in ["SUCCESS", "TIMEOUT"]:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": result.get("status") == "SUCCESS",
        "operation": "destroy",
        **result
    }


# -------------------------------
# TERRAFORM OUTPUT
# -------------------------------
@app.get("/terraform/output")
def tf_output():
    """Get Terraform outputs."""
    result = terraform_output()
    
    if result.get("status") != "SUCCESS":
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": True,
        "operation": "output",
        **result
    }


# -------------------------------
# TERRAFORM STATE
# -------------------------------
@app.get("/terraform/state")
def tf_state():
    """Show Terraform state."""
    result = terraform_state_show()
    
    if result.get("status") != "SUCCESS":
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "success": True,
        "operation": "show",
        **result
    }