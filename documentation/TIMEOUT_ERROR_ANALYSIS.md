# 🔴 TIMEOUT ERROR ANALYSIS - Agent Response Timing Out

## Executive Summary
**The Streamlit UI is timing out because the agent is attempting to wait for Jenkins builds to complete synchronously within a 180-second request window, while builds and LLM operations can easily exceed this timeframe.**

---

## Root Causes (Priority Order)

### 🔴 **CRITICAL: Build Completion Timeout Exceeds Streamlit Timeout**
**Location**: `adk_agent/agent.py` lines 170-184

```python
def wait_for_build_completion(job_name, build_number):
    timeout = 300  # 5 minutes!!! 
    start = time.time()
    while time.time() - start < timeout:
        # ... check status every 5 seconds ...
        time.sleep(5)
    return "TIMEOUT"
```

**Problem**:
- Waits up to **300 seconds** for build completion
- Streamlit timeout is only **180 seconds**
- If build takes 1-5 minutes (common), TIMEOUT occurs

**Impact**: Triggers every time user asks agent to run a job

---

### 🔴 **CRITICAL: Synchronous Build Execution Pattern**
**Location**: `adk_agent/agent.py` lines 233-245

```python
if tool_name == "trigger_build":
    # ... trigger build ...
    build_number = build_result.get("build_number")
    
    # ❌ WAITS FOR ENTIRE BUILD HERE
    final_status = wait_for_build_completion(matched_job, build_number)
    
    # ❌ THEN FETCHES LOGS
    logs_result = get_jenkins_logs(matched_job, build_number)
    
    # ❌ THEN CALLS LLM FOR SUMMARY
    summary = call_llm(summary_prompt)
```

**Problem**:
- Agent doesn't return until build is done
- Real Jenkins builds take 2-30+ minutes
- User waits indefinitely in Streamlit UI

**Expected Timeline for "trigger yahoo scraper"**:
1. LLM processing: ~10-20 seconds
2. Trigger build: ~1 second
3. **Wait for build: 5-30 minutes** ← USER WAITING
4. Fetch logs: ~2 seconds
5. LLM summary: ~20-30 seconds

**Total**: Often exceeds 180 seconds

---

### 🟠 **HIGH: Multiple LLM Calls with Long Timeouts**
**Location**: `adk_agent/agent.py` lines 199-210 and again later

```python
# First call: 90 second timeout
llm_response = call_llm(user_prompt)

# ... if trigger_build ...
# Second call: 90 second timeout (inside summarization)
summary = call_llm(summary_prompt)
```

**Problem**:
- Each LLM call has 90 second timeout
- Ollama model might be cold-starting
- Two calls = potential 180 seconds alone
- Combined with build wait = exceeds 180s total

**Call Stack**:
```
Streamlit (180s) 
└─ Agent request
   ├─ call_llm() [90s] ← LLM initialization + inference
   ├─ wait_for_build_completion() [300s] ← EXCEEDS 180s timeout!
   ├─ get_jenkins_logs() [15s]
   └─ call_llm() [90s] ← Another LLM call
```

---

### 🟠 **HIGH: Ollama Model Not Ready**
**Location**: `docker-compose.yml` lines 75-102

```yaml
ollama-puller:
  entrypoint: |-
    /bin/bash -c "
    echo '[ollama-puller] Waiting 30s for Ollama server startup...'
    sleep 30                    # 30 second delay
    
    echo '[ollama-puller] Pulling llama3 model...'
    ollama pull llama3          # Download could take 5+ minutes
```

**Problems**:
1. Fixed 30-second sleep (inefficient)
2. Model download can take 5-10 minutes
3. First LLM request might find model still downloading
4. `OllamaLLM()` initialization might block/timeout

**Current flow**:
```
docker-compose up
↓
Ollama container starts
↓ (wait 30s)
ollama-puller starts downloading llama3 (~5+ min)
↓
Agent container starts (depends on ollama-puller: service_completed_successfully)
↓
Agent tries to use model immediately
```

If agent starts before model is fully loaded, `call_llm()` might get HTTP 500 errors or timeouts.

---

### 🟠 **HIGH: No Retry Logic for Ollama Initialization Failures**
**Location**: `adk_agent/agent.py` lines 24-35

```python
def init_llm():
    """Attempt to initialize the Ollama LLM client."""
    global llm
    if llm is not None:
        return llm  # Already initialized
    
    try:
        test_llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3")
        llm = test_llm
        print("✅ LLM client initialized")
        return llm
    except Exception as e:
        print(f"⚠️ LLM initialization attempted but failed: {e}")
        return None  # ← Returns None, no retry
```

**Problem**:
- No exponential backoff
- No retry with delays
- No health check
- If Ollama is slow, LLM stays `None` forever
- Fallback to HTTP endpoint which also times out

---

### 🟡 **MEDIUM: No Health Check Before Request**
**Location**: `adk_agent/agent.py` lines 40-90

```python
def call_llm(prompt_text: str):
    # ❌ No check if Ollama is ready
    # ❌ No check if model is loaded
    
    try:
        test_llm = init_llm()  # Might return None
        if test_llm:
            result = str(test_llm.invoke(full_prompt))  # Could timeout
```

**Problem**:
- No health check endpoint called first
- Could timeout waiting for model inference on cold start
- No connection pooling/keepalive

---

### 🟡 **MEDIUM: Inconsistent Timeout Values**
**Location**: Multiple files

| Component | Timeout | Issue |
|-----------|---------|-------|
| Streamlit | 180s | Too short for long builds |
| agent.py → build wait | 300s | Exceeds Streamlit timeout |
| agent.py → LLM call | 90s | Could timeout on cold model |
| jenkins_client.py → safe_request | 30s | Too short for Jenkins API |
| requests in agent.py | 15s | Tight for large log files |

---

## Error Scenarios

### Scenario 1: User Triggers Job
```
t=0s   : User → Streamlit: "run yahoo scraper"
t=0-10s : Agent → LLM: "what tool should I use?" → 10s
t=10s  : Agent → Jenkins: "trigger Yahoo-Stock-Scraper"
t=12s  : Jenkins: "Build #42 queued"
t=12s  : Agent: start waiting (5-minute timeout)
t=32s  : Build starts running (Jenkins was busy)
t=32s  : Polling for status...
t=37s  : Polling... (build still running)
t=42s  : Polling... 
t=47s  : Polling...
...
t=180s : ⚠️ Streamlit timeout triggered!
        Response never sent
        User sees "Request Timed Out"
```

### Scenario 2: Ollama Not Ready
```
t=0s   : Agent container starts
t=0s   : Agent calls run_agent()
t=0s   : Agent calls call_llm()
t=0s   : LLM tries OllamaLLM(base_url=...)
t=5s   : ollama-puller still downloading model
t=5s   : LLM request gets HTTP 500 or timeout
t=5s   : Fallback to HTTP /api/chat
t=30s  : HTTP request still waiting (model cold)
t=90s  : ⚠️ Timeout on HTTP fallback
t=90s  : Agent returns error
```

---

## Complete Timeout Chain Analysis

```
STREAMLIT TIMEOUT: 180 seconds
│
├─ Agent receives request
│  │
│  ├─ call_llm(user_prompt)
│  │  ├─ init_llm() — LLM initialization (~5-10s if cold)
│  │  └─ invoke() — LLM inference (~10-20s)
│  │  Total: 15-30s
│  │
│  ├─ trigger_jenkins_build()
│  │  └─ 1-2 seconds
│  │
│  ├─ wait_for_build_completion() ← ⚠️ UP TO 300 SECONDS!
│  │  ├─ Poll status every 5 seconds
│  │  └─ Wait for: SUCCESS, FAILURE, or TIMEOUT
│  │  Total: 1min - 300s (EXCEEDS 180s window!)
│  │
│  ├─ get_jenkins_logs()
│  │  └─ 1-5 seconds (depends on log size)
│  │
│  └─ call_llm(summary_prompt) ← SECOND LLM CALL
│     └─ 20-30 seconds
│
└─ ⚠️ TOTAL: 180s to 600s+ (exceeds Streamlit timeout!)
```

---

## Fix Priority

### 🔴 P0: Fix Build Timeout
- Reduce `wait_for_build_completion()` timeout from 300s to 60s
- OR make build trigger async (return immediately with job ID)
- Recommended: **BOTH** - async trigger + optional status polling

### 🔴 P1: Fix Ollama Cold Start
- Add health check before first LLM call
- Wait for model to be ready with exponential backoff
- Increase Ollama healthcheck start_period in docker-compose

### 🟠 P2: Fix LLM Call Timeouts
- Reduce 90s timeout to 45s (still reasonable for inference)
- Add LLM caching for repeated prompts
- Consider model warm-start on agent startup

### 🟠 P3: Fix Request Timeout Chain
- Reduce Streamlit timeout to 120s (reasonable for UI)
- Add background job handling
- Implement async response pattern

---

## Related Configuration Files

- `docker-compose.yml` — Ollama healthcheck needs tuning
- `streamlit/app.py` — Reduce request timeout to match realistic expectations
- `adk_agent/agent.py` — Main culprit (synchronous build wait)
- `fast_api/main.py` — FastAPI endpoint timeouts
- `fast_api/jenkins_client.py` — Jenkins API timeouts

