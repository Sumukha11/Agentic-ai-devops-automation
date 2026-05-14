"""Terraform client for OpenStack TripleO infrastructure deployment."""

import subprocess
import os
import json
from pathlib import Path
from typing import Dict, Optional

TERRAFORM_DIR = os.getenv("TERRAFORM_DIR", "/app/terraform")


def run_terraform_command(command: str, var_file: Optional[str] = None) -> Dict:
    """Execute terraform command and return result."""
    try:
        # Ensure terraform directory exists
        if not os.path.exists(TERRAFORM_DIR):
            return {
                "error": f"Terraform directory not found: {TERRAFORM_DIR}",
                "status": "FAILED"
            }

        # Build command
        cmd = ["terraform", "-chdir=" + TERRAFORM_DIR, command]
        
        # Add var file if provided
        if var_file and os.path.exists(os.path.join(TERRAFORM_DIR, var_file)):
            cmd.extend(["-var-file", var_file])

        print(f"🔧 Executing: {' '.join(cmd)}")

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "command": command,
                "stdout": result.stdout,
                "message": f"Terraform {command} completed successfully"
            }
        else:
            return {
                "status": "FAILED",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": f"Terraform {command} failed",
                "return_code": result.returncode
            }

    except subprocess.TimeoutExpired:
        return {
            "error": "Terraform command timed out (5 minutes)",
            "status": "TIMEOUT",
            "command": command
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "ERROR",
            "command": command
        }


def terraform_init(backend_config: Optional[Dict] = None) -> Dict:
    """Initialize Terraform working directory."""
    try:
        cmd = ["terraform", "-chdir=" + TERRAFORM_DIR, "init"]
        
        # Add backend config if provided
        if backend_config:
            for key, value in backend_config.items():
                cmd.extend(["-backend-config", f"{key}={value}"])

        print(f"📦 Initializing Terraform: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "operation": "init",
                "message": "Terraform initialized successfully",
                "stdout": result.stdout
            }
        else:
            return {
                "status": "FAILED",
                "operation": "init",
                "error": result.stderr,
                "stdout": result.stdout
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "init",
            "error": str(e)
        }


def terraform_plan(var_file: str = "terraform.tfvars") -> Dict:
    """Generate and show an execution plan."""
    try:
        tfvars_path = os.path.join(TERRAFORM_DIR, var_file)
        if not os.path.exists(tfvars_path):
            return {
                "status": "FAILED",
                "operation": "plan",
                "error": f"Variables file not found: {var_file}"
            }

        cmd = [
            "terraform", "-chdir=" + TERRAFORM_DIR, "plan",
            "-var-file", var_file,
            "-out=tfplan"
        ]

        print(f"📋 Planning Terraform changes: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "operation": "plan",
                "message": "Terraform plan generated successfully",
                "stdout": result.stdout,
                "plan_file": "tfplan"
            }
        else:
            return {
                "status": "FAILED",
                "operation": "plan",
                "error": result.stderr,
                "stdout": result.stdout
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "plan",
            "error": str(e)
        }


def terraform_apply(auto_approve: bool = False, var_file: str = "terraform.tfvars") -> Dict:
    """Apply the changes required to reach the desired state."""
    try:
        tfvars_path = os.path.join(TERRAFORM_DIR, var_file)
        if not os.path.exists(tfvars_path):
            return {
                "status": "FAILED",
                "operation": "apply",
                "error": f"Variables file not found: {var_file}"
            }

        cmd = [
            "terraform", "-chdir=" + TERRAFORM_DIR, "apply",
            "-var-file", var_file
        ]

        if auto_approve:
            cmd.append("-auto-approve")

        print(f"🚀 Applying Terraform configuration: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for apply
            input="yes\n" if not auto_approve else ""
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "operation": "apply",
                "message": "OpenStack TripleO infrastructure deployed successfully!",
                "stdout": result.stdout
            }
        else:
            return {
                "status": "FAILED",
                "operation": "apply",
                "error": result.stderr,
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "operation": "apply",
            "error": "Terraform apply timed out (10 minutes). Infrastructure deployment may still be in progress."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "apply",
            "error": str(e)
        }


def terraform_destroy(auto_approve: bool = False, var_file: str = "terraform.tfvars") -> Dict:
    """Destroy all remote objects managed by the Terraform configuration."""
    try:
        tfvars_path = os.path.join(TERRAFORM_DIR, var_file)
        if not os.path.exists(tfvars_path):
            return {
                "status": "FAILED",
                "operation": "destroy",
                "error": f"Variables file not found: {var_file}"
            }

        cmd = [
            "terraform", "-chdir=" + TERRAFORM_DIR, "destroy",
            "-var-file", var_file
        ]

        if auto_approve:
            cmd.append("-auto-approve")

        print(f"🗑️ Destroying Terraform infrastructure: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for destroy
            input="yes\n" if not auto_approve else ""
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "operation": "destroy",
                "message": "OpenStack TripleO infrastructure destroyed successfully!",
                "stdout": result.stdout
            }
        else:
            return {
                "status": "FAILED",
                "operation": "destroy",
                "error": result.stderr,
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "operation": "destroy",
            "error": "Terraform destroy timed out (10 minutes). Infrastructure teardown may still be in progress."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "destroy",
            "error": str(e)
        }


def terraform_output() -> Dict:
    """Get the outputs from terraform state."""
    try:
        cmd = ["terraform", "-chdir=" + TERRAFORM_DIR, "output", "-json"]

        print(f"📤 Getting Terraform outputs")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                outputs = json.loads(result.stdout)
                return {
                    "status": "SUCCESS",
                    "operation": "output",
                    "outputs": outputs,
                    "message": "Terraform outputs retrieved successfully"
                }
            except json.JSONDecodeError:
                return {
                    "status": "SUCCESS",
                    "operation": "output",
                    "stdout": result.stdout,
                    "message": "Terraform outputs (raw)"
                }
        else:
            return {
                "status": "FAILED",
                "operation": "output",
                "error": result.stderr
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "output",
            "error": str(e)
        }


def terraform_state_show() -> Dict:
    """Show the current state of resources."""
    try:
        cmd = ["terraform", "-chdir=" + TERRAFORM_DIR, "show", "-json"]

        print(f"📊 Showing Terraform state")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                state = json.loads(result.stdout)
                return {
                    "status": "SUCCESS",
                    "operation": "show",
                    "resources_count": len(state.get("values", {}).get("root_module", {}).get("resources", [])),
                    "message": "Terraform state retrieved successfully",
                    "resource_types": list(set([
                        r["type"] for r in state.get("values", {}).get("root_module", {}).get("resources", [])
                    ]))
                }
            except json.JSONDecodeError:
                return {
                    "status": "SUCCESS",
                    "operation": "show",
                    "stdout": result.stdout
                }
        else:
            return {
                "status": "FAILED",
                "operation": "show",
                "error": result.stderr
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "operation": "show",
            "error": str(e)
        }
