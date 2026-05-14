# Testing Guide - Terraform Integration

## Pre-Testing Checklist

Before testing, ensure:

- [ ] Docker containers are running
- [ ] FastAPI server is accessible (`curl http://localhost:8000/`)
- [ ] Ollama is running and llama3 model is available
- [ ] Terraform is installed in fastapi container (`terraform version`)
- [ ] Terraform directory exists and has scripts
- [ ] SSH public key is configured in `terraform/terraform.tfvars`
- [ ] Streamlit app is running

---

## Test Scenarios

### SECTION A: Jenkins Operations (Verify Existing Functionality)

#### Test A1: List Jenkins Jobs
```
STEP 1: Open Streamlit UI
STEP 2: Input: "list jobs"
STEP 3: Wait for response (should be ~2 seconds)

EXPECTED OUTPUT:
- ✅ Response type: Chat message OR list
- ✅ Shows "Available Jenkins Jobs"
- ✅ Lists at least: api_healthcheck, git_repo_clone, yahoo_scraper

PASS/FAIL: ___________
```

#### Test A2: Trigger Jenkins Build
```
STEP 1: Input: "run api health check"
STEP 2: Wait for response

EXPECTED OUTPUT:
- ✅ Response: "✅ Build Triggered"
- ✅ Shows job name: "API-Health-Check" (or similar)
- ✅ Shows build number (e.g., "#42")
- ✅ Shows status: "QUEUED" or "TRIGGERED"
- ✅ Shows next step suggestion

PASS/FAIL: ___________
```

#### Test A3: Check Build Status
```
STEP 1: Input: "check status"
STEP 2: Wait for response

EXPECTED OUTPUT:
- ✅ Shows job name
- ✅ Shows build number
- ✅ Shows status (QUEUED, BUILDING, SUCCESS, or FAILURE)
- ✅ If SUCCESS: shows ✅ emoji and duration

PASS/FAIL: ___________
```

---

### SECTION B: Terraform Intent Detection (NEW)

#### Test B1: Terraform Keyword Recognition
```
STEP 1: Input: "initialize terraform"
STEP 2: Wait for response (~10 seconds for actual terraform command)

EXPECTED OUTPUT:
- ✅ Agent routes to terraform_init (not jenkins)
- ✅ Response starts with: "✅ Terraform initialized" or "📦 Terraform"
- ✅ No Jenkins-related messages

VERIFICATION:
- Check agent logs: `docker logs <agent-container> | grep terraform_init`
- Should show: "✅ Valid tool: terraform_init"

PASS/FAIL: ___________
```

#### Test B2: Infrastructure Keywords Recognition
```
STEP 1: Input: "deploy openstack infrastructure"
STEP 2: Observe agent decision

EXPECTED OUTPUT:
- ✅ Agent detects "openstack" + "infrastructure"
- ✅ Routes to terraform tools (not jenkins)
- ✅ May ask to initialize first

VERIFICATION:
Check if agent triggered terraform operations in logs

PASS/FAIL: ___________
```

#### Test B3: Ambiguous Request
```
STEP 1: Input: "what can you do?"
STEP 2: Wait for response

EXPECTED OUTPUT:
- ✅ Response explains BOTH Jenkins AND Terraform
- ✅ Mentions CI/CD and infrastructure deployment
- ✅ Asks which user prefers (if truly ambiguous)

PASS/FAIL: ___________
```

---

### SECTION C: Terraform Operations (NEW)

#### Test C1: Terraform Initialization
```
STEP 1: Input: "setup terraform"
STEP 2: Wait 10-15 seconds

EXPECTED OUTPUT:
- ✅ Response: "✅ Terraform Initialized" or "📦 Terraform initialized successfully"
- ✅ No error messages about missing terraform directory

DEBUGGING IF FAILS:
- Check terraform directory: `ls -la terraform/`
- Check terraform in container: `docker exec <fastapi> terraform version`
- Check logs: `docker logs <fastapi-container> | tail -20`

PASS/FAIL: ___________
```

#### Test C2: Terraform Plan (Preview Changes)
```
STEP 1: First run: "setup terraform" (if not done)
STEP 2: Input: "plan the deployment"
STEP 3: Wait 30-60 seconds

EXPECTED OUTPUT:
- ✅ Response contains: "📋 Terraform Plan Generated"
- ✅ Shows list of resources to be created (e.g., "8 resources")
- ✅ Mentions VM types, networks, storage
- ✅ Next steps suggest to "apply terraform"

DEBUGGING IF FAILS:
- Check terraform.tfvars exists: `ls terraform/terraform.tfvars`
- Check terraform syntax: `terraform -chdir=terraform validate`
- Check logs: `docker logs <fastapi> | grep terraform_plan`

PASS/FAIL: ___________
```

#### Test C3: Terraform Apply (Deploy Infrastructure)
```
STEP 1: Input: "apply terraform" or "deploy infrastructure"
STEP 2: Wait 10-20 MINUTES (deployment time)
STEP 3: Check back periodically

⚠️ IMPORTANT: This will create real VMs on the system!

EXPECTED OUTPUT:
- ✅ Response: "🚀 Infrastructure Deployed Successfully!"
- ✅ OR if timeout: "⚠️ Deployment may still be in progress"
- ✅ Later checks show "📊 Terraform state" with resources

CLEANUP AFTER TEST:
- Input: "destroy infrastructure"
- Wait 5-15 minutes for cleanup

DEBUGGING IF FAILS:
- Check libvirt: `virsh list` (should work on host)
- Check terraform state: `terraform -chdir=terraform state list`
- Check error logs: `docker logs <fastapi> | grep ERROR`

PASS/FAIL: ___________
```

#### Test C4: Terraform Outputs
```
STEP 1: After successful deploy, input: "show terraform outputs"
STEP 2: Wait 5 seconds

EXPECTED OUTPUT:
- ✅ Response: "📤 Terraform Outputs"
- ✅ Shows deployment endpoints
- ✅ Shows IP addresses or other output values
- ✅ Shows undercloud_ip, controller_ips, etc.

PASS/FAIL: ___________
```

#### Test C5: Terraform State
```
STEP 1: Input: "show terraform state"
STEP 2: Wait 5 seconds

EXPECTED OUTPUT:
- ✅ Response: "📊 Terraform State"
- ✅ Shows number of managed resources
- ✅ Lists resource types (libvirt_domain, libvirt_network, etc.)
- ✅ Example: "Resources Managed: 8"

PASS/FAIL: ___________
```

#### Test C6: Terraform Destroy
```
STEP 1: Input: "destroy infrastructure"
STEP 2: Wait 5-15 MINUTES for cleanup

EXPECTED OUTPUT:
- ✅ Response: "🗑️ Infrastructure Destroyed Successfully!"
- ✅ OR if timeout: "⚠️ Teardown may still be in progress"
- ✅ All VMs should be removed
- ✅ Networks should be removed

VERIFICATION:
- Check VMs: `virsh list` (should be empty)
- Check terraform state: `terraform -chdir=terraform state list` (should be empty)

PASS/FAIL: ___________
```

---

### SECTION D: UI/UX Testing (NEW)

#### Test D1: Sidebar Help
```
STEP 1: Look at Streamlit sidebar
STEP 2: Check if sections exist

EXPECTED OUTPUT:
- ✅ Section: "📦 Jenkins CI/CD"
- ✅ Section: "🏗️ Terraform Infrastructure"
- ✅ Examples for both
- ✅ Tips section

PASS/FAIL: ___________
```

#### Test D2: Chat Input Placeholder
```
STEP 1: Look at chat input box
STEP 2: Check placeholder text

EXPECTED OUTPUT:
- ✅ Shows: "Try: 'list jobs' or 'deploy openstack infrastructure'"
- ✅ Suggests both Jenkins and Terraform examples

PASS/FAIL: ___________
```

#### Test D3: Response Formatting
```
STEP 1: Trigger various operations
STEP 2: Check response format

EXPECTED OUTPUT:
- ✅ Jenkins responses: Use ✅ emoji
- ✅ Terraform responses: Use 📋 📤 🚀 🗑️ emoji
- ✅ Errors: Use ❌ emoji
- ✅ All responses are properly formatted markdown

PASS/FAIL: ___________
```

#### Test D4: Message History
```
STEP 1: Perform 3-4 operations
STEP 2: Refresh browser page

EXPECTED OUTPUT:
- ✅ Chat history is preserved
- ✅ All previous messages still visible
- ✅ Timestamps or order is logical

PASS/FAIL: ___________
```

---

### SECTION E: Error Handling (NEW)

#### Test E1: Missing Terraform Directory
```
STEP 1: (Admin) Rename terraform directory temporarily
STEP 2: Input: "initialize terraform"
STEP 3: Wait for response

EXPECTED OUTPUT:
- ✅ Response contains error message
- ✅ Error is clear: "Terraform directory not found" or similar
- ✅ Suggests solution

STEP 4: (Admin) Restore terraform directory

PASS/FAIL: ___________
```

#### Test E2: Invalid Variables
```
STEP 1: (Admin) Remove or corrupt terraform.tfvars
STEP 2: Input: "plan deployment"
STEP 3: Wait for response

EXPECTED OUTPUT:
- ✅ Response contains error
- ✅ Error mentions "variables" or "tfvars"
- ✅ Suggests to check configuration

STEP 4: (Admin) Restore terraform.tfvars

PASS/FAIL: ___________
```

#### Test E3: Timeout on Long Operation
```
STEP 1: Input: "deploy infrastructure" or "destroy infrastructure"
STEP 2: Wait beyond normal response time (> 120 seconds)

EXPECTED OUTPUT:
- ✅ Eventually shows: "⚠️ Request Timed Out"
- ✅ Suggests to check status later
- ✅ Deployment/teardown may still be ongoing

PASS/FAIL: ___________
```

#### Test E4: Agent Unavailable
```
STEP 1: (Admin) Stop agent container: `docker stop <agent-container>`
STEP 2: In Streamlit, input: Any prompt
STEP 3: Wait for response

EXPECTED OUTPUT:
- ✅ Response: "❌ Connection Error"
- ✅ Message suggests checking agent container

STEP 4: (Admin) Restart agent: `docker start <agent-container>`

PASS/FAIL: ___________
```

---

## Comprehensive Test Sequence (Full Workflow)

### Quick Full Test (No Infrastructure)
```
⏱️ Duration: ~5-10 minutes

1. ✅ List Jenkins jobs
2. ✅ What can you do?
3. ✅ Initialize terraform
4. ✅ Plan terraform deployment
5. ✅ Show terraform state (should be empty)
6. ✅ Show terraform outputs (should be empty)
```

### Complete Deployment Test (With Infrastructure)
```
⏱️ Duration: ~30-45 minutes total

1. ✅ List Jenkins jobs (verify working)
2. ✅ Initialize terraform (30 seconds)
3. ✅ Plan deployment (1 minute)
4. ✅ Deploy infrastructure (15-20 minutes) ← LONGEST
5. ✅ Show outputs (get IPs/endpoints)
6. ✅ Show state (verify resources)
7. ✅ Destroy infrastructure (5-10 minutes)
8. ✅ Verify state is empty
```

---

## Logging & Debugging

### View Agent Logs
```bash
docker logs -f agentic_ai_devops_tools-agent-1 | grep -E "(terraform|jenkins|Valid tool)"
```

### View FastAPI Logs
```bash
docker logs -f agentic_ai_devops_tools-fastapi-1 | grep -E "(terraform|Executing)"
```

### Check Terraform Directory
```bash
ls -la terraform/
cat terraform/terraform.tfvars
```

### Manual Terraform Commands
```bash
# In terraform directory
terraform init
terraform plan
terraform apply -auto-approve
terraform destroy -auto-approve
```

---

## Success Criteria

### All tests pass if:
- [ ] Jenkins operations work as before (baseline)
- [ ] Terraform operations execute without errors
- [ ] Intent detection correctly routes to Jenkins or Terraform
- [ ] UI displays responses with proper formatting
- [ ] Error messages are helpful and actionable
- [ ] Response times are reasonable (<5 seconds for LLM decisions)
- [ ] Infrastructure deployment completes successfully (if tested)
- [ ] Chat history is preserved across refreshes

---

## Test Report Template

```
DATE: __________________
TESTER: ________________
SYSTEM: ________________

SECTION A - Jenkins Operations:    PASS / FAIL
SECTION B - Intent Detection:      PASS / FAIL
SECTION C - Terraform Operations:  PASS / FAIL
SECTION D - UI/UX:                 PASS / FAIL
SECTION E - Error Handling:        PASS / FAIL

OVERALL: ✅ PASS / ❌ FAIL

ISSUES FOUND:
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

NOTES:
___________________________________________
___________________________________________
```

---

## Quick Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent doesn't respond to terraform | Ollama not ready | Wait 30s, restart agent |
| "terraform: command not found" | Not installed in container | `apt-get install terraform` |
| Plan/Apply times out | Normal for infrastructure | Check status later with "show state" |
| "Connection refused" | FastAPI not running | `docker-compose up fastapi` |
| "Invalid var_file" | terraform.tfvars missing/corrupt | Check file exists and has valid syntax |
| Jenkins operations fail | Separate issue (baseline) | Check Jenkins/FastAPI logs |

---

## Next Steps

After testing:

1. ✅ All tests pass → Ready for production
2. ⚠️ Some tests fail → Review logs and troubleshooting guide
3. 🔧 Need to adjust → Update configurations and retry specific tests
4. 📝 Document findings → Submit test report

---

**Happy Testing! 🚀**
