import os
import json
import requests
import streamlit as st

AGENT_URL = os.getenv("AGENT_URL", "http://agent:8100/query")

st.set_page_config(page_title="AI DevOps Assistant", layout="wide")

st.title("🤖 AI DevOps Assistant")
st.caption("AI-powered Jenkins Automation & Build Analysis")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Try: list jobs, run api check, trigger all jobs")

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

                    elif "ai_summary" in result:
                        job_name = result.get("job", "Unknown Job")
                        final_status = result.get("final_status", "UNKNOWN")
                        build_number = result.get("build_number", "N/A")

                        status_emoji = "✅"
                        if final_status == "FAILURE":
                            status_emoji = "❌"
                        elif final_status == "TIMEOUT":
                            status_emoji = "⚠️"

                        summary = result.get("ai_summary", "No summary available.")

                        reply = f"""{status_emoji} **Job Analysis Complete**

### 📦 Job
`{job_name}`

### 🔢 Build Number
`{build_number}`

### 📊 Final Status
`{final_status}`

---

### 🤖 AI Analysis

{summary}"""

                    elif result.get("status") == "QUEUED":
                        job_name = result.get("job", "Unknown Job")
                        build_number = result.get("build_number", "N/A")
                        info = result.get("info", "")
                        
                        reply = f"""✅ **Build Triggered**

### 📦 Job
`{job_name}`

### 🔢 Build Number
`{build_number}`

### 📊 Status
`QUEUED` (Build is running)

---

{info}

You can ask me to check the status anytime!"""

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
- **List jobs**: "list jobs" or "what jobs are available"
- **Trigger one**: "run api health check" or "trigger scraper"
- **Trigger all**: "run all jobs" or "trigger everything"
- **Trigger multiple**: "run scraper and git clone" or "trigger health check and scraper"
- **Check status**: "check status" or "what's the build status"

### Tips
- Be specific with job names
- You can ask for multiple jobs in one request
- Use natural language - I'll understand!
""")
