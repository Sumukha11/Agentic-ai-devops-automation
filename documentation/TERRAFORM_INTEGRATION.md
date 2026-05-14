# Terraform Integration Guide

## Overview

The AI DevOps Assistant now supports both **Jenkins CI/CD automation** and **Terraform Infrastructure as Code** for deploying OpenStack TripleO architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI                              │
│              (streamlit/app.py)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent (adk_agent/agent.py)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ - Processes user natural language input             │   │
│  │ - Routes to Jenkins OR Terraform based on intent    │   │
│  │ - Uses Ollama LLM for decision making               │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         ▼                          ▼
┌─────────────────────┐    ┌──────────────────────┐
│  FastAPI Backend    │    │   FastAPI Backend    │
│  (fast_api/main.py) │    │  (fast_api/main.py)  │
├─────────────────────┤    ├──────────────────────┤
│ Jenkins Endpoints   │    │ Terraform Endpoints  │
│ - /jobs             │    │ - /terraform/init    │
│ - /build            │    │ - /terraform/plan    │
│ - /status           │    │ - /terraform/apply   │
│ - /logs             │    │ - /terraform/destroy │
│                     │    │ - /terraform/output  │
│                     │    │ - /terraform/state   │
└──────────┬──────────┘    └──────────┬───────────┘
           │                          │
           ▼                          ▼
       Jenkins         Terraform + libvirt + KVM
```

## Components Added

### 1. Terraform Client (`fast_api/terraform_client.py`)
- Handles Terraform command execution via subprocess
- Provides functions for:
  - `terraform_init()` - Initialize Terraform working directory
  - `terraform_plan()` - Generate execution plan
  - `terraform_apply()` - Deploy infrastructure
  - `terraform_destroy()` - Tear down infrastructure
  - `terraform_output()` - Retrieve outputs
  - `terraform_state_show()` - Show current state

### 2. FastAPI Terraform Endpoints (`fast_api/main.py`)
```python
POST /terraform/init       # Initialize terraform
POST /terraform/plan       # Plan infrastructure changes
POST /terraform/apply      # Apply configuration
POST /terraform/destroy    # Destroy infrastructure
GET  /terraform/output     # Get outputs
GET  /terraform/state      # Show state
```

### 3. Updated Agent (`adk_agent/agent.py`)
- New tools:
  - `terraform_init` - Initialize
  - `terraform_plan` - Preview changes
  - `terraform_apply` - Deploy
  - `terraform_destroy` - Tear down
  - `terraform_output` - Show outputs
  - `terraform_state` - Show state
- Updated system prompt to ask Jenkins vs Terraform
- Intent detection to route user requests appropriately

### 4. Enhanced Streamlit UI (`streamlit/app.py`)
- Terraform-specific response handlers
- Updated sidebar with Terraform examples
- Deployment status tracking
- Infrastructure state visualization

## Usage Examples

### Jenkins Operations
```
User: "list all jobs"
→ Agent triggers: terraform_list_jobs
→ Response: Shows available Jenkins jobs

User: "run api health check"
→ Agent triggers: terraform_trigger_build
→ Response: Build triggered with number

User: "check status"
→ Agent triggers: terraform_get_status
→ Response: Current build status
```

### Terraform Operations
```
User: "initialize terraform"
→ Agent triggers: terraform_init
→ Response: ✅ Terraform initialized

User: "plan openstack deployment"
→ Agent triggers: terraform_plan
→ Response: 📋 Plan shows what will be created

User: "deploy infrastructure"
→ Agent triggers: terraform_apply
→ Response: 🚀 Deployment started

User: "show deployment details"
→ Agent triggers: terraform_output
→ Response: 📤 Shows IP addresses, endpoints, etc.

User: "destroy infrastructure"
→ Agent triggers: terraform_destroy
→ Response: 🗑️ Cleanup completed
```

### Mixed Scenarios
```
User: "what can you do?"
→ Agent triggers: chat tool
→ Response: Lists both Jenkins and Terraform capabilities

User: "should I use jenkins or terraform?"
→ Agent triggers: chat tool
→ Response: Explains use cases for each
```

## Intent Detection Logic

The agent uses the following logic to detect user intent:

**→ Jenkins Operations:**
- Keywords: "jenkins", "build", "job", "trigger", "CI/CD", "pipeline", "deploy job"
- Operations: List jobs, trigger builds, check status, view logs

**→ Terraform Operations:**
- Keywords: "terraform", "infrastructure", "deploy", "IaC", "openstack", "tripleo", "plan", "apply", "destroy"
- Operations: Init, plan, apply, destroy, show state, get outputs

**→ Ambiguous/General:**
- Ask user to clarify: "Would you like to use Jenkins for CI/CD or Terraform for infrastructure deployment?"

## Terraform Variables

The Terraform scripts use the following key variables (from `terraform/terraform.tfvars`):

```hcl
# Connection
libvirt_uri = "qemu:///system"

# SSH
ssh_public_key = "[YOUR_SSH_PUBLIC_KEY]"

# Base image
base_image_url = "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2"

# Undercloud (1 node)
undercloud_vcpus = 4
undercloud_memory_mb = 16384
undercloud_disk_gb = 100

# Overcloud Controllers (3 nodes)
controller_count = 3
controller_vcpus = 4
controller_memory_mb = 16384
controller_disk_gb = 100

# Overcloud Computes (1+ nodes)
compute_count = 1
compute_vcpus = 4
compute_memory_mb = 16384
compute_disk_gb = 100
```

## Workflow Examples

### Complete Infrastructure Deployment

1. **Initialize:**
   ```
   User: "Setup terraform for openstack"
   → terraform_init executed
   ```

2. **Plan:**
   ```
   User: "Show me what will be deployed"
   → terraform_plan executed
   → Shows resources to be created
   ```

3. **Review & Confirm:**
   ```
   User: "Go ahead and deploy"
   → terraform_apply executed
   → Infrastructure created
   ```

4. **Check Deployment:**
   ```
   User: "Show me the deployment details"
   → terraform_output executed
   → Shows IPs, endpoints, connection info
   ```

5. **Monitor State:**
   ```
   User: "What resources do we have?"
   → terraform_state executed
   → Shows all managed resources
   ```

6. **Cleanup (Optional):**
   ```
   User: "Tear down the infrastructure"
   → terraform_destroy executed
   → All resources removed
   ```

### Jenkins Pipeline with Terraform

1. **List Jobs:**
   ```
   User: "Show jenkins jobs"
   → Lists all available jobs
   ```

2. **Trigger Job:**
   ```
   User: "Run the api health check"
   → Job triggered
   ```

3. **Check Result:**
   ```
   User: "Is the build done?"
   → Shows current status
   ```

## Error Handling

The system handles various error scenarios:

1. **Terraform Directory Not Found**
   - Response: Shows missing directory error
   - Solution: Ensure `/app/terraform` exists with Terraform files

2. **Variables File Missing**
   - Response: Shows missing `terraform.tfvars` error
   - Solution: Ensure variables file exists in terraform directory

3. **Libvirt Connection Failed**
   - Response: Shows connection error
   - Solution: Ensure KVM/libvirt is available on host system

4. **Timeout on Long Operations**
   - terraform_plan: 5 minute timeout
   - terraform_apply: 10 minute timeout
   - terraform_destroy: 10 minute timeout
   - Response: Shows timeout warning but deployment may still be in progress

5. **Jenkins Connection Failed**
   - Response: Shows Jenkins connection error
   - Solution: Ensure Jenkins URL is correct in environment variables

## Environment Variables

Set these in `.env` or `docker-compose.yml`:

```bash
# Agent
FASTAPI_URL=http://fastapi:8000
OLLAMA_URL=http://ollama:11434
AGENT_URL=http://agent:8100/query

# Terraform (optional)
TERRAFORM_DIR=/app/terraform  # Default path to terraform scripts
```

## File Structure

```
.
├── adk_agent/
│   ├── agent.py          # Main agent (UPDATED)
│   ├── main.py
│   └── requirements.txt
├── fast_api/
│   ├── main.py           # FastAPI app (UPDATED)
│   ├── terraform_client.py # NEW - Terraform operations
│   ├── jenkins_client.py
│   └── requirements.txt
├── streamlit/
│   ├── app.py            # Streamlit UI (UPDATED)
│   └── requirements.txt
├── terraform/
│   ├── main.tf           # Main infrastructure
│   ├── variable.tf       # Variables
│   ├── terraform.tfvars  # Variable values
│   ├── undercloud.tf
│   ├── overcloud_nodes.tf
│   ├── network.tf
│   ├── storage.tf
│   └── outputs.tf
└── documentation/
    └── TERRAFORM_INTEGRATION.md # THIS FILE
```

## Testing

### Test Jenkins Integration
```
Prompt: "list jobs"
Expected: Shows all Jenkins jobs

Prompt: "run api health check"
Expected: Build triggered with number
```

### Test Terraform Integration
```
Prompt: "initialize terraform"
Expected: ✅ Terraform initialized

Prompt: "plan openstack deployment"
Expected: 📋 Shows planned resources

Prompt: "apply terraform"
Expected: 🚀 Deployment started

Prompt: "show terraform outputs"
Expected: 📤 Shows deployment endpoints
```

### Test Intent Routing
```
Prompt: "what can you do"
Expected: Lists both Jenkins and Terraform capabilities

Prompt: "deploy my app"
Expected: Asks clarification - Jenkins or Terraform?
```

## Troubleshooting

### Issue: "Terraform directory not found"
**Solution:** 
- Ensure `TERRAFORM_DIR` environment variable is set correctly
- Default is `/app/terraform`
- Check that terraform files exist in that directory

### Issue: "terraform: command not found"
**Solution:**
- Ensure Terraform is installed in the container
- Add to Dockerfile:
  ```dockerfile
  RUN apt-get install -y terraform
  ```

### Issue: "libvirt connection refused"
**Solution:**
- Ensure KVM/libvirt is available on host
- Check libvirt URI in terraform.tfvars
- May need to run with `--privileged` flag in Docker

### Issue: Agent doesn't respond to Terraform commands
**Solution:**
- Check agent logs: `docker logs <agent-container>`
- Verify FastAPI is running: `curl http://fastapi:8000/`
- Check Ollama is responding: `curl http://ollama:11434/api/tags`

### Issue: Terraform apply times out
**Solution:**
- Normal for large deployments
- Check status: "show terraform state"
- May need to increase timeout in `terraform_client.py`

## Next Steps

1. **Customize Variables:** Update `terraform/terraform.tfvars` with your requirements
2. **Add More Jobs:** Create additional Jenkins jobs as needed
3. **Extend Tools:** Add more Terraform workspaces or alternative infrastructures
4. **Integration:** Connect to existing CI/CD pipelines or monitoring tools
5. **Security:** Add authentication/authorization for production use

## References

- [Terraform Documentation](https://www.terraform.io/docs)
- [TripleO Documentation](https://docs.openstack.org/tripleo-docs/)
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Ollama Documentation](https://github.com/jmorganca/ollama)
