import os
import streamlit as st
import requests
import time

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8100/query")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="AI DevOps Assistant", layout="wide")

st.title("🤖 AI DevOps Assistant")
st.caption("Chat-based Jenkins Automation")

# ---------------------------
# SESSION STATE
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------
# DISPLAY CHAT HISTORY
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# INPUT
# ---------------------------
prompt = st.chat_input("Try: run api_healthcheck or list jobs")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------------------
    # CALL AGENT
    # ---------------------------
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            try:
                res = requests.post(
                    AGENT_URL,
                    json={"prompt": prompt},
                    timeout=60
                )

                api_response = res.json()
                response = api_response.get("response")
                
                # Handle case where response is a string representation of dict
                if isinstance(response, str):
                    try:
                        response = eval(response)
                    except:
                        pass

                # ---------------------------
                # HANDLE RESPONSE
                # ---------------------------
                if isinstance(response, dict):

                    # ---------------------------
                    # 📋 JOB LIST
                    # ---------------------------
                    if "jobs" in response:
                        jobs = response["jobs"]

                        reply = "📋 **Available Jobs:**\n\n"
                        for job in jobs:
                            reply += f"- `{job}`\n"

                        st.markdown(reply)

                    # ---------------------------
                    # ❌ ERROR
                    # ---------------------------
                    elif "error" in response:
                        reply = f"❌ {response['error']}"
                        st.markdown(reply)

                    # ---------------------------
                    # 🚀 TRIGGERED FLOW
                    # ---------------------------
                    elif "build_number" in response or ("job" in response and "status" in response):

                        job_name = response.get("job")
                        build_number = response.get("build_number")

                        st.markdown(f"🚀 **Job Triggered:** `{job_name}`")
                        if build_number:
                            st.markdown(f"🔢 **Build Number:** `{build_number}`")
                        else:
                            st.markdown("🔢 **Build Number:** `pending`")

                        status_placeholder = st.empty()
                        logs_placeholder = st.empty()

                        start_time = time.time()
                        timeout = 120  # seconds
                        final_status = "TRIGGERED"

                        status_placeholder.markdown(
                            f"📊 **Status:** `{final_status}` (triggered)"
                        )

                        # if no build number, wait for last status and get it
                        if not build_number:
                            wait_start = time.time()
                            last_res = None
                            while time.time() - wait_start < timeout:
                                time.sleep(2)
                                last_res = requests.get(
                                    f"{FASTAPI_URL}/status/{job_name}/last"
                                ).json()
                                bnum = last_res.get("build_number")
                                status_k = last_res.get("status") or "RUNNING"

                                status_placeholder.markdown(
                                    f"⏳ **Waiting for build number...** status: `{status_k}`"
                                )

                                if bnum:
                                    build_number = bnum
                                    st.markdown(f"🔢 **Detected Build Number:** `{build_number}`")
                                    break

                                # if previous build completed (e.g. SUCCESS/FAILURE) and build number still missing,
                                # attempt to read from last build anyway
                                if status_k in ["SUCCESS", "FAILURE"] and last_res is not None:
                                    build_number = last_res.get("build_number")
                                    if build_number:
                                        st.markdown(f"🔢 **Detected Build Number from completed build:** `{build_number}`")
                                        break

                            # if still no build number after timeout, set to last if available
                            if not build_number and last_res is not None:
                                build_number = last_res.get("build_number")
                                if build_number:
                                    st.markdown(f"🔢 **Fallback Build Number:** `{build_number}` (may be last completed build)")

                        # ---------------------------
                        # 🔁 POLLING LOOP
                        # ---------------------------
                        while True:
                            time.sleep(2)

                            # ---- STATUS ----
                            if build_number:
                                status_res = requests.get(
                                    f"{FASTAPI_URL}/status/{job_name}/{build_number}"
                                ).json()
                            else:
                                status_res = requests.get(
                                    f"{FASTAPI_URL}/status/{job_name}/last"
                                ).json()

                            final_status = status_res.get("status")

                            # Handle None → RUNNING
                            if final_status is None:
                                final_status = "RUNNING"

                            status_placeholder.markdown(
                                f"📊 **Status:** `{final_status}`"
                            )

                            # ---- LOGS ----
                            if build_number:
                                logs_res = requests.get(
                                    f"{FASTAPI_URL}/logs/{job_name}/{build_number}"
                                ).json()
                            else:
                                # no build number yet, attempt last build logs fallback
                                last_status = requests.get(
                                    f"{FASTAPI_URL}/status/{job_name}/last"
                                ).json()
                                last_build_number = last_status.get("build_number")
                                if last_build_number:
                                    logs_res = requests.get(
                                        f"{FASTAPI_URL}/logs/{job_name}/{last_build_number}"
                                    ).json()
                                else:
                                    logs_res = {"logs": "Waiting for first build to start..."}

                            logs = logs_res.get("logs")
                            if not logs and "message" in logs_res:
                                logs = logs_res.get("message")

                            # Show a rolling console window with latest lines
                            if logs:
                                display_lines = logs.splitlines()
                                if len(display_lines) > 25:
                                    display_lines = display_lines[-25:]
                                logs_placeholder.code("\n".join(display_lines))
                            else:
                                logs_placeholder.code("Fetching console output...")

                            # ---- EXIT CONDITIONS ----
                            if final_status in ["SUCCESS", "FAILURE"]:
                                break

                            if time.time() - start_time > timeout:
                                final_status = "TIMEOUT"
                                break

                        # ---------------------------
                        # FINAL MESSAGE
                        # ---------------------------
                        if final_status == "SUCCESS":
                            reply = "✅ **Build Succeeded**"
                        elif final_status == "FAILURE":
                            reply = "❌ **Build Failed**"
                        elif final_status == "TIMEOUT":
                            reply = "⚠️ **Build Timed Out**"
                        else:
                            reply = f"⚠️ **Unknown Status: {final_status}**"

                        # final logs (full or large sample)
                        if build_number:
                            final_logs_res = requests.get(
                                f"{FASTAPI_URL}/logs/{job_name}/{build_number}"
                            ).json()
                            final_logs = final_logs_res.get("logs", "")
                            if final_logs:
                                st.markdown("📄 **Final console output:**")
                                st.code("\n".join(final_logs.splitlines()[-200:]))

                        st.markdown(reply)

                    # ---------------------------
                    # ℹ️ MESSAGE
                    # ---------------------------
                    elif "message" in response:
                        reply = f"ℹ️ {response['message']}"
                        st.markdown(reply)

                    # ---------------------------
                    # FALLBACK
                    # ---------------------------
                    else:
                        reply = str(response)
                        st.markdown(reply)

                else:
                    reply = str(response)
                    st.markdown(reply)

            except requests.exceptions.Timeout:
                reply = "⚠️ Error: Request timed out. Agent may be starting up."
                st.markdown(reply)
            except Exception as e:
                reply = f"⚠️ Error: {str(e)}"
                st.markdown(reply)

    # ---------------------------
    # SAVE RESPONSE
    # ---------------------------
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })