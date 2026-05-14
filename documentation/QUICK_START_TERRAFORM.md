# Quick Start Guide - Terraform Integration

## 🎯 Overview

Your AI DevOps Assistant now supports **both Jenkins CI/CD and Terraform Infrastructure as Code**. The agent automatically detects your intent and uses the appropriate tool.

## 🚀 Quick Examples

### Jenkins Operations
```
📋 List all jobs
User: "list jobs" or "what jobs do we have?"
Agent Response: Shows available Jenkins jobs

▶️ Run a build
User: "run api health check" or "trigger git clone"
Agent Response: Build queued with build number

✅ Check build status  
User: "check status" or "is the build done?"
Agent Response: Current build status and details
```

### Terraform Operations
```
🏗️ Deploy OpenStack Infrastructure
User: "deploy openstack" or "initialize terraform then plan"
Steps:
  1. Initialize Terraform
  2. Generate deployment plan
  3. Review changes
  4. Apply deployment
Agent Response: Shows deployment progress and details

📊 View Deployment Details
User: "show terraform outputs"
Agent Response: IPs, endpoints, connection information

🗑️ Cleanup Infrastructure
User: "destroy infrastructure"
Agent Response: Confirmation and cleanup status
```

### Decision Trees
```
User: "what can you do?"
→ Agent explains both Jenkins and Terraform options

User: "deploy my app"
→ Agent asks: Jenkins or Terraform?

User: "show me the infrastructure"
→ Agent knows you mean Terraform and shows state
```

## 🔧 Common Commands

### Planning Your Infrastructure
```
User: "plan the openstack deployment"
→ Agent shows what will be created:
  - 1 Undercloud VM (4 vCPU, 16GB RAM)
  - 3 Controller nodes
  - 1+ Compute nodes
  - Network configuration
```

### Deploying Infrastructure
```
User: "deploy the infrastructure"
→ Agent applies terraform configuration:
  - Creates VMs
  - Configures networking
  - Sets up storage
  - Returns access details

⏱️ Typical time: 10-15 minutes
```

### Monitoring Deployment
```
User: "show me the current state"
→ Agent displays:
  - Number of resources
  - Resource types
  - Resource status

User: "show deployment details"
→ Agent displays:
  - IP addresses
  - Hostnames
  - Connection endpoints
  - Access credentials
```

### Tearing Down
```
User: "destroy everything"
→ Agent removes all resources:
  - VMs deleted
  - Networks removed
  - Storage cleaned up
  - Clean slate ready for new deployment
```

## 📝 Advanced Usage

### With Parameters
```
User: "plan deployment with custom compute nodes"
→ Agent can use terraform.tfvars to customize:
  - Number of compute nodes
  - VM CPU count
  - Memory allocation
  - Storage size
```

### Checking Logs
```
User: "show me the deployment logs"
→ Agent displays terraform output showing:
  - Creation events
  - Network setup
  - Resource IDs
  - Any errors or warnings
```

## 🎓 Decision Logic

### The Agent Understands Context

**→ Mention "Jenkins" or "CI/CD"?**
- Lists Jenkins jobs
- Triggers builds
- Checks build status
- Views build logs

**→ Mention "Terraform" or "Infrastructure"?**
- Initializes terraform
- Plans infrastructure
- Applies configuration
- Shows deployment state

**→ Ambiguous?**
- "I can help with Jenkins CI/CD or Terraform Infrastructure. Which would you like?"

## ⚙️ Environment Setup

Make sure these are configured:

```bash
# FastAPI backend
FASTAPI_URL=http://fastapi:8000

# Ollama LLM
OLLAMA_URL=http://ollama:11434

# Terraform location
TERRAFORM_DIR=/app/terraform

# Your SSH public key for VM access
SSH_PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2E..."
```

## 📚 Documentation

- **Full Guide:** [TERRAFORM_INTEGRATION.md](../documentation/TERRAFORM_INTEGRATION.md)
- **Terraform Variables:** [terraform.tfvars](../terraform/terraform.tfvars)
- **Architecture:** See README.md

## 🆘 Common Issues

### Issue: "Terraform not found"
**Solution:** Ensure terraform is installed:
```bash
terraform version
```

### Issue: "Connection to libvirt failed"
**Solution:** KVM/libvirt must be available. Check:
```bash
virsh list
```

### Issue: "Agent timeouts on deployment"
**Solution:** Terraform apply can take 10+ minutes. This is normal!
- Ask status later: "show terraform state"
- Or check outputs: "show deployment details"

### Issue: "My variables aren't being used"
**Solution:** Make sure `terraform.tfvars` exists and is readable in the terraform directory.

## 💡 Best Practices

1. **Always Plan First**
   - "plan the deployment" before "apply terraform"
   - Review what will be created

2. **Save Outputs**
   - "show terraform outputs" to get connection details
   - Save IPs and endpoints for later use

3. **Test with Small Scale**
   - Start with 1 compute node
   - Scale up once infrastructure is stable

4. **Clean Up**
   - "destroy infrastructure" when done
   - Saves resources and costs

5. **Version Control**
   - Keep terraform.tfvars in git
   - Track infrastructure-as-code changes

## 🔗 Quick Links

- Jenkins Documentation: https://www.jenkins.io/doc/
- Terraform Documentation: https://www.terraform.io/docs
- OpenStack TripleO: https://docs.openstack.org/tripleo-docs/
- Ollama: https://github.com/jmorganca/ollama

---

**Ready to try?**

1. Open the Streamlit app
2. Type: "What can you do?"
3. Choose Jenkins or Terraform
4. Follow the agent's guidance!
