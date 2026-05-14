import os
import json
import requests
import streamlit as st

AGENT_URL = os.getenv("AGENT_URL", "http://agent:8100/query")

st.set_page_config(page_title="AI DevOps Assistant", layout="wide")

st.title("🤖 AI DevOps Assistant")
st.caption("AI-powered Jenkins Automation, Terraform IaC & OpenStack TripleO Deployment")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Try: 'list jobs' or 'deploy openstack infrastructure'")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Lamma is analyzing your request..."):
            try:
                response = requests.post(
                    AGENT_URL,
                    json={"prompt": prompt},
                    timeout=120
                )

                api_response = response.json()
                result = api_response.get("response")

                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except Exception:
                        pass

                reply = ""

                if isinstance(result, dict):

                    if "error" in result:
                        reply = f"❌ **Error**\n\n{result['error']}"

                    elif "jobs" in result:
                        jobs = result.get("jobs", [])
                        reply = "📋 **Available Jenkins Jobs**\n\n"
                        for job in jobs:
                            reply += f"- `{job}`\n"

                    elif result.get("status") in ["QUEUED", "TRIGGERED"]:
                        job_name = result.get("job", "Unknown Job")
                        build_number = result.get("build_number", "N/A")
                        info = result.get("info", "")
                        
                        reply = f"""✅ **Build Triggered**

### 📦 Job
`{job_name}`

### 🔢 Build Number
`{build_number}`

### 📊 Status
`{result.get('status')}`

---

{info}

You can ask me to check the status anytime!"""

                    elif result.get("job") and result.get("status"):
                        job_name = result.get("job", "Unknown Job")
                        build_number = result.get("build_number", "N/A")
                        status = result.get("status", "UNKNOWN")
                        building = result.get("building")
                        duration = result.get("duration")
                        info = result.get("message", "Status retrieved successfully.")

                        status_emoji = "✅"
                        if status == "FAILURE":
                            status_emoji = "❌"
                        elif status == "RUNNING":
                            status_emoji = "⚠️"

                        reply = f"""{status_emoji} **Build Status**

### 📦 Job
`{job_name}`

### 🔢 Build Number
`{build_number}`

### 📊 Status
`{status}`
"""
                        if building is not None:
                            reply += f"\n### 🛠️ Building\n`{building}`\n"
                        if duration is not None:
                            reply += f"\n### ⏱️ Duration\n`{duration}` ms\n"
                        reply += f"\n---\n\n{info}"

                    elif "triggered_jobs" in result:
                        triggered = result.get("triggered_jobs", [])
                        failed = result.get("failed_jobs", [])
                        
                        reply = "✅ **Multiple Builds Triggered**\n\n"
                        
                        if triggered:
                            reply += "### ✅ Successfully Triggered:\n"
                            for job_info in triggered:
                                job = job_info.get("job", "Unknown")
                                bn = job_info.get("build_number", "N/A")
                                reply += f"- `{job}` → Build #{bn}\n"
                        
                        if failed:
                            reply += "\n### ❌ Failed:\n"
                            for job in failed:
                                reply += f"- `{job}`\n"
                        
                        info = result.get("info", "Check status anytime!")
                        reply += f"\n---\n\n{info}"

                    elif result.get("operation") == "terraform_init":
                        status = result.get("status", "UNKNOWN")
                        message = result.get("message", "")
                        
                        if status == "SUCCESS":
                            reply = f"""✅ **Terraform Initialized**

{message}

---

Ready to plan and deploy OpenStack TripleO infrastructure!"""
                        else:
                            error = result.get("error", "Unknown error")
                            reply = f"❌ **Terraform Init Failed**\n\n{error}"

                    elif result.get("operation") == "terraform_plan":
                        status = result.get("status", "UNKNOWN")
                        message = result.get("message", "")
                        
                        if status == "SUCCESS":
                            reply = f"""📋 **Terraform Plan Generated**

{message}

---

**Next Steps:**
1. Review the plan above
2. Ask me to apply the changes: "apply terraform"
3. Or ask me to destroy: "destroy infrastructure"

**Note:** Changes will not be made until you approve the apply operation."""
                        else:
                            error = result.get("error", "Unknown error")
                            reply = f"❌ **Terraform Plan Failed**\n\n{error}"

                    elif result.get("operation") == "terraform_apply":
                        status = result.get("status", "UNKNOWN")
                        message = result.get("message", "")
                        
                        if status == "SUCCESS":
                            reply = f"""🚀 **Infrastructure Deployed Successfully!**

{message}

**Status:** ✅ OpenStack TripleO deployment complete

---

**Next Steps:**
- Ask me to check outputs: "show terraform outputs"
- Ask me to check state: "show terraform state"
- Ask me to destroy: "destroy infrastructure"

The VMs and network infrastructure should now be provisioned."""
                        elif status == "TIMEOUT":
                            reply = f"""⚠️ **Terraform Apply Timeout**

{message}

**Note:** The deployment may still be in progress. Check back in a few minutes or ask me to show the current state."""
                        else:
                            error = result.get("error", "Unknown error")
                            reply = f"❌ **Terraform Apply Failed**\n\n{error}"

                    elif result.get("operation") == "terraform_destroy":
                        status = result.get("status", "UNKNOWN")
                        message = result.get("message", "")
                        
                        if status == "SUCCESS":
                            reply = f"""🗑️ **Infrastructure Destroyed Successfully!**

{message}

**Status:** ✅ All resources have been cleaned up

---

Ready to deploy new infrastructure or perform other operations."""
                        elif status == "TIMEOUT":
                            reply = f"""⚠️ **Terraform Destroy Timeout**

{message}

**Note:** The teardown may still be in progress. Check back in a few minutes."""
                        else:
                            error = result.get("error", "Unknown error")
                            reply = f"❌ **Terraform Destroy Failed**\n\n{error}"

                    elif result.get("operation") == "terraform_output":
                        status = result.get("status", "UNKNOWN")
                        outputs = result.get("outputs", {})
                        
                        if status == "SUCCESS" and outputs:
                            reply = "📤 **Terraform Outputs**\n\n"
                            for key, value in outputs.items():
                                if isinstance(value, dict):
                                    val = value.get("value", value)
                                else:
                                    val = value
                                reply += f"**{key}:**\n```\n{json.dumps(val, indent=2)}\n```\n\n"
                        else:
                            reply = f"📤 **Terraform Outputs**\n\n{result.get('stdout', 'No outputs found')}"

                    elif result.get("operation") == "terraform_state":
                        status = result.get("status", "UNKNOWN")
                        resources_count = result.get("resources_count", 0)
                        resource_types = result.get("resource_types", [])
                        
                        if status == "SUCCESS":
                            reply = f"""📊 **Terraform State**

**Resources Managed:** {resources_count}

**Resource Types:**
"""
                            for rtype in resource_types:
                                reply += f"- `{rtype}`\n"
                        else:
                            reply = f"❌ **Failed to retrieve state**\n\n{result.get('error', 'Unknown error')}"

                    elif "message" in result:
                        reply = f"ℹ️ {result['message']}"

                    else:
                        reply = f"⚠️ Unexpected response format\n\n```json\n{json.dumps(result, indent=2)}\n```"

                else:
                    reply = str(result)

            except requests.exceptions.Timeout:
                reply = """⚠️ Request Timed Out

The AI agent may still be:
- loading the model
- waiting for Jenkins
- analyzing logs

Please try again in a few seconds."""

            except requests.exceptions.ConnectionError:
                reply = """❌ Connection Error

Could not connect to the AI agent.

Please verify:
- agent container is running
- Ollama is healthy
- Docker networking is working"""

            except Exception as e:
                reply = f"❌ Unexpected Error\n\n{str(e)}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

st.sidebar.markdown("""
### How to Use

#### 📦 **Jenkins CI/CD**
- **List jobs**: "list jobs" or "what jobs are available"
- **Trigger one**: "run api health check" or "trigger scraper"
- **Check status**: "check status" or "what's the build status"
- **View logs**: "show logs for job X"

#### 🏗️ **Terraform Infrastructure**
- **Initialize**: "initialize terraform" or "setup terraform"
- **Plan**: "plan openstack deployment" or "preview infrastructure"
- **Apply**: "deploy infrastructure" or "apply terraform"
- **Destroy**: "destroy infrastructure" or "tear down openstack"
- **Show outputs**: "show deployment details" or "terraform outputs"
- **Show state**: "show infrastructure state" or "terraform state"

### Tips
- Be specific with job names (Jenkins)
- Ask about infrastructure changes (Terraform shows you what will change before applying)
- Use natural language - I understand both Jenkins and Terraform contexts!
- Only one Jenkins job can be triggered at a time
""")

