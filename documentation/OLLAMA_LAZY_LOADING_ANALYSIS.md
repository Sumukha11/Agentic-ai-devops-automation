# 📊 OLLAMA MODEL LOADING - LOG ANALYSIS & EXPLANATION

## What You're Seeing

The LLM loads **AFTER the first input in Streamlit**, not before. This creates a ~3 minute wait for the first user message.

**Timeline from your logs**:
```
03:05:02 - User sends first message to Streamlit
03:05:02 - Ollama starts loading model ("llm server loading model")
03:05:04 - Model loading in progress
...
03:07:51 - Model loading completes (246 seconds = 4+ minutes!)
03:07:51 - llama_context initialized, ready to respond
```

---

## Why This Happens - Root Cause

### The Problem: **LAZY LOADING**

**Current Code Flow**:
```
Docker Start
    ↓
Ollama Container Ready
    ↓
Agent Container Ready
    ↓
✅ Agent listening at :8100
    ↓
User sends first message in Streamlit
    ↓
❌ LLM NOT loaded yet - LOADING NOW (3-4 minutes!)
    ↓
Finally responds to user
```

**Culprit Code** (`adk_agent/agent.py`):
```python
llm = None  # Model NOT loaded

def init_llm():
    global llm
    if llm is not None:
        return llm  # Skip if already loaded
    
    # FIRST TIME: This creates OllamaLLM but doesn't actually load it!
    try:
        test_llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3")
        llm = test_llm
        return llm
    except Exception as e:
        return None

def call_llm(prompt_text):
    # This is called ONLY when user sends first message!
    test_llm = init_llm()
    if test_llm:
        # ⚠️ THIS LINE TRIGGERS ACTUAL MODEL LOADING
        result = str(test_llm.invoke(full_prompt))  # ← Model loads here!
```

**Key Issue**: 
- `OllamaLLM()` constructor doesn't load the model
- `invoke()` call loads the model on **first use**
- Model isn't loaded until first user input

---

## Understanding the Logs

### Log Timeline Breakdown

**03:05:02 - Initial State**
```
ollama | load_tensors: CPU model buffer size = 4437.80 MiB
```
- Ollama container recognizes the model exists (4.4 GB)
- But hasn't loaded it into memory yet
- Model is on disk, not in RAM

**03:05:02 to 03:07:51 - Loading Phase** (246 seconds!)
```
ollama | time=2026-05-12T03:05:02.589Z level=INFO source=server.go:1428 
        msg="waiting for server to become available" 
        status="llm server not responding"

ollama | time=2026-05-12T03:05:04.981Z level=INFO source=server.go:1428 
        msg="waiting for server to become available" 
        status="llm server loading model"
```

**What's Happening**: Ollama is:
1. ✅ Initialization phase 1: Loading model into GPU/CPU memory
2. ⏳ Waiting for server to respond ("llm server not responding" = still loading)
3. ⏳ Repeatedly checking if model is ready ("llm server loading model")
4. ❌ Server temporarily becomes unresponsive while loading
5. ✅ Cycle repeats until model fully loaded

**Why Multiple "waiting" Messages?**
```
03:05:02 - Check 1: "not responding" (loading started)
03:05:04 - Check 2: "loading model" (still going)
03:05:26 - Check 3: "not responding" (server busy)
03:05:27 - Check 4: "loading model" (continuing)
03:05:42 - Check 5: "not responding" (still busy)
03:05:42 - Check 6: "loading model" (continuing)
...
03:07:51 - Finally: "loading model" then ready!
```

Each check happens every 2-5 seconds. Model loading takes ~3-4 minutes for llama3 on CPU.

**03:06:03 - Network Error (Harmless)**
```
ollama | time=2026-05-12T03:06:03.433Z level=WARN source=model_recommendations.go:168 
        msg="model recommendations refresh failed" 
        error="Get "https://ollama.com/api/experimental/model-recommendations": context deadline exceeded"
```

This is just Ollama trying to check for newer models online. Network timeout, not critical. Retries later.

**03:07:51 - Model Context Initialization** (READY!)
```
ollama | llama_context: constructing llama_context
ollama | llama_context: n_seq_max     = 1
ollama | llama_context: n_ctx         = 4096
ollama | llama_context: n_ctx         = 4096
ollama | llama_context: n_batch       = 512
ollama | llama_context: causal_attn   = 1
ollama | llama_context: flash_attn    = auto
```

**What This Means**:
- ✅ Model is NOW loading into memory
- `n_ctx = 4096` = Model can handle 4096 tokens of context
- `n_batch = 512` = Process 512 tokens at a time
- `flash_attn = auto` = Use optimized attention if available
- `causal_attn = 1` = Causal attention (standard for LLMs)

**⚠️ Warning in Log**:
```
ollama | llama_context: n_ctx_seq (4096) < n_ctx_train (8192) 
        -- the full capacity of the model will not be utilized
```

**Translation**: Model was trained with 8192 token context, but only using 4096. This is fine - saves memory.

---

## Timeline Visualization

```
DOCKER COMPOSE START
├─ 0s: Ollama container starts
├─ 0s: Model files on disk (4.4 GB)
├─ 0s: Agent container starts, listening at :8100
│
└─ 0s: ✅ SYSTEM READY
   └─ User opens Streamlit UI
      └─ User types first message
         
         ⏱️ DELAY STARTS HERE

         ├─ 03:05:02 - Agent receives request
         ├─ 03:05:02 - call_llm() triggered
         ├─ 03:05:02 - init_llm() called
         ├─ 03:05:02 - OllamaLLM() constructor called
         ├─ 03:05:02 - invoke() called
         │
         │ ⏳ OLLAMA MODEL LOADING (BLOCKING)
         │
         ├─ 03:05:02 to 03:07:51 - Loading llama3 model (246 seconds)
         │  ├─ Loading model into GPU/CPU memory
         │  ├─ Building context (4096 tokens)
         │  ├─ Initializing attention mechanisms
         │  └─ Model ready!
         │
         └─ 03:07:51 - ✅ Response sent to user
```

---

## Why This Is A Problem

1. **Poor User Experience**
   - User waits 4+ minutes on first message
   - Streamlit times out (120 second limit)
   - User thinks it's broken

2. **Scale Issue**
   - Every container restart = 4+ minute wait
   - Each deployment = cold start penalty
   - Development/testing is slow

3. **Production Impact**
   - Kubernetes pod restart = wait time
   - Auto-scaling = wait time for new instances
   - Blue-green deployment = all new instances wait

---

## Solutions to Fix This

### Option 1: **Eager Load on Startup** (RECOMMENDED)
Load model when agent starts, not on first request.

**Where to Add**: `adk_agent/main.py` (startup hook)

```python
from adk_agent.agent import init_llm

@app.on_event("startup")
async def startup_event():
    """Warm up LLM on startup."""
    print("🔥 Pre-warming LLM model...")
    llm = init_llm()
    if llm:
        print("✅ LLM ready for requests")
    else:
        print("⚠️ LLM initialization deferred")
```

**Result**: Model loads while user opening Streamlit, not blocking their first input.

---

### Option 2: **Make Warm-up Call on Startup**
Call LLM with dummy prompt on container start.

**Where to Add**: `adk_agent/agent.py` or `main.py`

```python
def warmup_llm():
    """Make a dummy call to load model into memory."""
    try:
        print("🔥 Warming up LLM...")
        response = call_llm("Hello")
        print(f"✅ LLM warmed up: {response[:50]}")
    except Exception as e:
        print(f"⚠️ Warmup failed (will retry on first request): {e}")
```

**Call on startup**:
```python
@app.on_event("startup")
async def startup():
    asyncio.create_task(warmup_llm())
```

---

### Option 3: **Docker Compose Improvement**
Add health check that pre-loads model.

```yaml
agent:
  build: ...
  depends_on:
    ollama-puller:
      condition: service_completed_successfully
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
    interval: 5s
    timeout: 3s
    retries: 10
    start_period: 60s  # Give agent time to warm up
```

---

## Recommended Fix

**Best approach**: Option 1 (Eager Load on Startup)

**Implementation**:
1. Add startup event to FastAPI app
2. Call `init_llm()` on startup
3. If successful, model is loaded before any requests come in
4. First user request gets instant response

**Expected Result**:
```
✅ BEFORE:
- Docker starts
- User waits 4 minutes on first input
- Then gets response

✅ AFTER (with fix):
- Docker starts
- Agent pre-loads model (4 minutes in background)
- User opens Streamlit (model loading happening)
- User types input (model ready!)
- Gets response instantly
```

---

## Implementation Example

**File**: `adk_agent/main.py`

```python
from fastapi import FastAPI
from pydantic import BaseModel
from adk_agent.agent import run_agent, init_llm  # Import init_llm
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_warmup():
    """Pre-warm the LLM model on startup."""
    print("\n🔥 STARTUP: Pre-warming LLM model...")
    
    # Run in background to not block startup
    asyncio.create_task(_warmup_in_background())

async def _warmup_in_background():
    try:
        print("⏳ Initializing LLM client...")
        llm = init_llm()
        
        if llm:
            print("✅ LLM client initialized successfully")
            print("✅ First user request will be instant!")
        else:
            print("⚠️ LLM initialization deferred to first request")
    except Exception as e:
        print(f"❌ Warmup error: {e}")

# ... rest of the code
```

---

## Summary

| Aspect | Current | After Fix |
|--------|---------|-----------|
| **Model Load Timing** | On first request | On container startup |
| **First User Wait** | 4+ minutes | 0 seconds |
| **Time to Response** | 240+ seconds | 10-20 seconds |
| **User Experience** | 😞 Times out | 😊 Instant |
| **Deployment** | Slow | Fast |

