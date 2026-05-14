# IITP 3rd Semester Project: Agentic AI DevOps Tools - Complete Architecture Documentation

**Project Title:** Agentic AI DevOps Tools with Jenkins Automation & Terraform IaC  
**Version:** 3.0  
**Last Updated:** May 2026  
**Technology Stack:** Docker, Kubernetes-style Orchestration, FastAPI, Streamlit, Ollama LLM, Jenkins CI/CD, Terraform, OpenStack TripleO

---

## Table of Contents

1. [🆕 Terraform Integration (NEW)](#terraform-integration-new)
2. [Recent Updates & Improvements](#recent-updates--improvements)
3. [Project Overview](#project-overview)
4. [Architecture Diagram](#architecture-diagram)
5. [System Components](#system-components)
6. [Data Flow](#data-flow)
7. [Technology Stack Details](#technology-stack-details)
8. [Deployment & Orchestration](#deployment--orchestration)
9. [API Specifications](#api-specifications)
10. [LLM Integration](#llm-integration)
11. [Security & Configuration](#security--configuration)
12. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🆕 Terraform Integration (NEW)

**Version 3.0 now includes Terraform support for OpenStack TripleO infrastructure deployment!**

### What's New
- **Dual-Mode Operation:** Choose between Jenkins CI/CD or Terraform IaC based on your needs
- **Natural Language Routing:** Agent automatically routes to Jenkins or Terraform based on your intent
- **Infrastructure as Code:** Deploy and manage OpenStack TripleO clusters via Terraform
- **Streamlined UI:** Terraform operations integrated into existing Streamlit interface

### Quick Start
```
User: "deploy openstack infrastructure"
→ Agent initializes Terraform and creates deployment plan

User: "show terraform outputs"  
→ Agent retrieves deployment endpoints and IPs

User: "destroy infrastructure"
→ Agent tears down all managed resources
```

**📖 [Complete Terraform Integration Guide](documentation/TERRAFORM_INTEGRATION.md)**

### Key Features
- ✅ Initialize Terraform working directory
- ✅ Plan infrastructure changes before applying
- ✅ Deploy OpenStack TripleO architecture
- ✅ Monitor deployment state
- ✅ Retrieve deployment outputs (IPs, endpoints)
- ✅ Teardown infrastructure on demand

### Supported Terraform Operations
| Operation | Command | Use Case |
|-----------|---------|----------|
| `init` | "initialize terraform" | Setup Terraform working directory |
| `plan` | "plan deployment" | Preview infrastructure changes |
| `apply` | "deploy infrastructure" | Create/update OpenStack resources |
| `destroy` | "destroy infrastructure" | Remove all managed resources |
| `output` | "show deployment details" | Get IPs, endpoints, connection info |
| `state` | "show terraform state" | View managed resources |

---

## Recent Updates & Improvements

### Version 3.0 - May 2026 - Terraform Infrastructure Integration

#### ✨ New Features:
- **Terraform Client** (`fast_api/terraform_client.py`) - Handles all terraform operations
- **6 New FastAPI Endpoints** - `/terraform/init`, `/terraform/plan`, `/terraform/apply`, `/terraform/destroy`, `/terraform/output`, `/terraform/state`
- **6 New Agent Tools** - terraform_init, terraform_plan, terraform_apply, terraform_destroy, terraform_output, terraform_state
- **Intent Detection** - Automatically routes Jenkins vs Terraform requests
- **Enhanced UI** - Terraform operation visualization in Streamlit

#### 🔧 Key Improvements:
- **Smart Routing:** Agent determines Jenkins or Terraform based on keywords and context
- **Timeout Handling:** Terraform operations can take 10+ minutes with proper timeout handling
- **State Management:** Track and display infrastructure state
- **Output Display:** Show deployment endpoints and configuration details

---

### Version 2.1 - April 2026 - Comprehensive Fixes & Optimizations

#### ✅ 1. **Timeout Issues - RESOLVED**
**Problem:** Streamlit UI timing out after 180 seconds  
**Root Cause:** Agent was synchronously waiting for Jenkins builds to complete (up to 5-30 minutes) before returning response

**Fixes Applied:**
- **Asynchronous Build Triggering:** Agent now returns immediately after queuing build instead of waiting for completion
  - Old: Block for 1-30+ minutes → Timeout
  - New: Return in 1-2 seconds with `"status": "QUEUED"`
- **Reduced LLM Timeouts:** `90s → 45s` with configurable parameters
- **Individual Request Timeouts Optimized:**
  - `list_jenkins_jobs()`: `15s → 10s`
  - `trigger_jenkins_build()`: `15s → 10s`
  - `get_jenkins_status()`: `15s → 10s`
  - `get_jenkins_logs()`: `15s → 20s` (reasonable for large logs)
  - Individual poll timeout: `15s → 10s`
- **Exponential Backoff for LLM Initialization:** Retries 3 times with 2s, 4s, 8s delays for better cold-start handling
- **Streamlit Timeout Reduced:** `180s → 120s` for faster failure feedback

**Impact:** System now responsive in <2 seconds for immediate feedback; users can monitor builds asynchronously

---

#### ✅ 2. **LLM Hallucination & Job Triggering - RESOLVED**
**Problem:** LLM returning JSON examples instead of actual tool calls, causing job triggering to fail

**Root Causes:**
- System prompt examples were too similar to actual outputs
- Agent code only handled single `job_name`, not `job_names` array
- JSON validation too permissive (accepted wrong structure)

**Fixes Applied:**
- **Completely Rewrote System Prompt:**
  - Added explicit "NEVER OUTPUT EXAMPLES" warning
  - Strict guardrails against hallucination
  - Clear distinction between VALID and INVALID responses
  - Multi-job detection rules
  - NO examples showing array syntax (single examples only)
  - Emphasis: Response = ONLY JSON, NO TEXT BEFORE/AFTER

- **Added Batch Job Support:**
  - New tool: `trigger_builds` (plural) for multiple job triggering
  - Multi-job detection logic:
    - "all jobs" OR "every job" → `trigger_builds` with ALL available
    - "multiple jobs" OR "few jobs" → `trigger_builds`
    - "X and Y" → `trigger_builds` with both
    - Single job → `trigger_build`

- **Enhanced JSON Validation:**
  - Validates structure (not just parsing)
  - Checks required keys exist
  - Validates tool names against whitelist: `[list_jobs, trigger_build, trigger_builds, get_status, get_logs, chat]`
  - Proper error logging for debugging
  - Fallback to chat tool on invalid structure

**New Agent Logic for Multiple Jobs:**
```python
elif tool_name == "trigger_builds":
    # Iterate through requested jobs
    # Trigger each one individually
    # Collect results and failures
    # Return aggregated response with:
    #   - triggered_jobs: array of successful builds
    #   - failed_jobs: array of failed triggers
    #   - info: monitoring instructions
```

**Impact:** Jobs now trigger correctly; LLM no longer produces hallucinated responses; batch operations supported

---

#### ✅ 3. **Ollama Model Lazy Loading - RESOLVED**
**Problem:** 4+ minute delay on first user query while model loads from disk into memory

**Root Causes:**
- LLM initialization happened at agent startup, before model was ready
- No retry logic when Ollama not responding
- `depends_on: service_started` didn't verify model was actually loaded
- First user query triggered model loading (slow)

**Fixes Applied:**
- **Added ollama-puller Service:** One-shot job that:
  - Waits for Ollama HTTP endpoint ready (polls `/api/tags`)
  - Verifies model is available
  - Pre-pulls model before agent starts
  - Ensures model is in cache when agent initializes

- **Improved Agent Startup:**
  - `wait-for-ollama-ready.sh` entrypoint script
  - Polls Ollama `/api/tags` to verify model loaded
  - Exponential backoff: 2s, 4s, 8s delays
  - 120 retries (≈5-6 minutes max)
  - Allows proceeding if server up (model may load in background)

- **Enhanced call_llm() Function:**
  - Multiple HTTP endpoint variants: `/api/generate`, `/v1/completions`, `/v1/chat/completions`
  - Multiple payload format attempts
  - Better response parsing (extracts from various JSON structures)
  - Detailed logging of all attempts

**Docker Compose Changes:**
```yaml
ollama-puller:
  image: ollama/ollama:latest
  depends_on:
    ollama: { condition: service_started }
  entrypoint: [bash script that pulls model]
  restart: "no"  # Run once, don't auto-restart
  volumes:
    - ollama_data:/root/.ollama  # Shared with ollama

agent:
  depends_on:
    ollama-puller: { condition: service_completed_successfully }
  entrypoint: wait-for-ollama-ready.sh
```

**Impact:** Cold starts are pre-warmed; first user query no longer experiences 4+ minute delay

---

#### ✅ 4. **Docker Compose Variable Escaping & ollama-puller Service - RESOLVED**
**Problem:** `docker-compose up` failing with "ollama-puller didn't complete successfully: exit 1"

**Errors:**
```
WARN[0000] The "retry_count" variable is not set
WARN[0000] The "max_retries" variable is not set
✘ Container ollama-puller service "ollama-puller" didn't complete successfully
```

**Root Cause:**
- Inline bash script in Docker Compose used `$retry_count` 
- Docker Compose interpreted this as variable interpolation
- Variables weren't defined, became empty strings
- Resulted in invalid bash syntax: `[ -ge 60 ]`

**Fixes Applied:**
- **Variable Escaping:** Changed `$variable` to `$$variable`
  - In Docker Compose YAML: `$$` → escape sequence
  - `$$variable` → Docker processes to `$variable`
  - `$variable` → Bash processes for actual substitution

- **Simplified Script:** Replaced while-loop with for-loop
  ```bash
  # Old (complex with escaping issues):
  while ! curl ... ; do
    if [ $$retry_count -ge $$max_retries ]; then
      exit 1
    fi
    retry_count=$$(( $$retry_count + 1 ))
  done
  
  # New (simpler, more reliable):
  for i in {1..120}; do
    if curl ... ; then
      break
    fi
    if [ $$i -eq 120 ]; then
      exit 1
    fi
  done
  ```

- **Better Logging:** Added `[ollama-puller]` prefix for clarity in logs

- **Removed Obsolete version Attribute:** Removed `version: '3.8'` (deprecated in Docker Compose v2+)

**Expected Timeline After Fix:**
- 0-2min: Ollama starts
- 2-3min: ollama-puller waits for HTTP endpoint
- 3-5min: Ollama server ready
- 5-20min: llama2 model downloads (~3.8GB)
- 20min+: Agent starts, then Streamlit

**Impact:** Docker Compose deploys successfully; services initialize in correct order

---

#### ✅ 5. **LLM HTTP Fallback & Multiple Endpoint Support - RESOLVED**
**Problem:** Agent stuck in infinite loop when LLM client fails, no fallback to HTTP

**Root Causes:**
- `if llm:` guard prevented HTTP fallback when LLM object was None
- No retry mechanism if Ollama unavailable
- Single HTTP endpoint (if LLM client failed, no alternative)

**Fixes Applied:**
- **Removed LLM Guard:** Always attempt LLM calls for non-keyword queries
  - Old: `if llm: call_llm()` else return hardcoded response
  - New: Attempt call_llm() regardless; it handles failures internally

- **Multiple HTTP Endpoints:** call_llm() now tries:
  1. LangChain OllamaLLM client (if initialized)
  2. Direct HTTP `/api/generate`
  3. Direct HTTP `/v1/completions` (OpenAI-compatible)
  4. Direct HTTP `/v1/chat/completions` (OpenAI-compatible)

- **Multiple Payload Formats:**
  - `{"model": "llama2", "prompt": "..."}`
  - `{"model": "llama2", "messages": [...]}`
  - `{"model": "llama2", "input": "..."}`

- **Robust Response Parsing:** Extracts from:
  - `.response` field
  - `.text` field
  - `.output` field
  - `.choices[0].message.content` (OpenAI format)

- **Better Logging:** Logs all attempts and failures for debugging

**Impact:** Agent resilient to LLM connection issues; graceful degradation instead of hanging

---

#### ✅ 6. **Streamlit Response Handling - IMPROVED**
**Changes:**
- Added handler for `"status": "QUEUED"` responses (async build triggers)
- Better formatting for batch job responses
- Clearer UI feedback for build monitoring instructions
- Improved error message display

**Impact:** Users understand build is queued and know how to monitor progress

---

### Summary of Changes by Component

| Component | Change | Impact |
|-----------|--------|--------|
| `adk_agent/agent.py` | Async build triggers, reduced timeouts, exponential backoff LLM init | <2s response time instead of timeout |
| `adk_agent/main.py` | Response handler for async builds | Proper status updates to Streamlit |
| `adk_agent/Dockerfile` | Wait script, curl installation | Proper service startup sequencing |
| `adk_agent/wait-for-ollama-ready.sh` | NEW: Polls Ollama `/api/tags` | Cold-start pre-warming |
| `streamlit/app.py` | Reduced request timeout, QUEUED response handler | Faster UI feedback, better UX |
| `fast_api/main.py` + `jenkins_client.py` | Timeout parameter tuning | Faster individual operations |
| `docker-compose.yml` | Variable escaping fixes, ollama-puller service, agent depends_on | Reliable deployment |
| System Prompt | Complete rewrite, stricter guardrails | No more hallucination |

---

## Project Overview

### Purpose

The Agentic AI DevOps Tools project is a conversational CI/CD automation platform that integrates:
- **Large Language Model (LLM)** for natural language understanding via Ollama (Llama2)
- **Jenkins CI/CD** for build automation and pipeline management
- **FastAPI** for backend microservices
- **Streamlit** for interactive web-based user interface
- **Docker** for containerization and orchestration

### Core Capabilities

1. **Natural Language Interface**: Users can communicate in plain English with the AI agent
2. **Jenkins Automation**: Trigger builds, check job status, view logs, and list available jobs
3. **Intelligent Routing**: The AI determines user intent and routes commands appropriately
4. **Fallback Mechanisms**: Multiple layers of error handling ensure resilience
5. **Scalable Architecture**: Microservices design allows independent scaling

### Key Features

| Feature | Description |
|---------|-------------|
| **NLP-Driven Automation** | Llama2 LLM processes natural language commands |
| **Multi-Step Intelligence** | Agent routes queries to specialized handlers (Jenkins, status checks, logs) |
| **Robust Error Recovery** | Graceful fallbacks when services unavailable |
| **Real-time Feedback** | Streaming responses with detailed execution logging |
| **Extensible Design** | New capabilities can be added via agent routing |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          END USER INTERFACE LAYER                            │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Streamlit Web Application (Port 8501)                              │   │
│  │  - Interactive chat interface                                       │   │
│  │  - Message history management                                       │   │
│  │  - Response formatting (jobs list, build confirmations, logs)       │   │
│  └──────────────────────────┬──────────────────────────────────────────┘   │
└─────────────────────────────┼──────────────────────────────────────────────┘
                              │ HTTP POST /query {"prompt": "..."}
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT & ORCHESTRATION LAYER                               │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Agent Service (FastAPI on Port 8100)                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Main Components:                                           │  │   │
│  │  │  • Query Receiver: POST /query endpoint                     │  │   │
│  │  │  • Intent Router: Keyword detection + NLP analysis          │  │   │
│  │  │  • LLM Interface: Direct Ollama HTTP + LangChain client     │  │   │
│  │  │  • Jenkins Connector: Via FastAPI backend                  │  │   │
│  │  │  • Error Handler: Fallback to structured responses         │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                    ▼ (Depends on services below)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                     │
└──────────────────────────┼─────────────────────┼────────────────────────────┘
                           │                     │
        ┌──────────────────┴─┐            ┌─────┴─────────────┐
        │                    │            │                   │
        ▼                    ▼            ▼                   ▼
┌──────────────────┐  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐
│  FastAPI Backend │  │  Ollama LLM  │  │  Jenkins CI/CD │  │   Debug UI   │
│  (Port 8000)     │  │  (Port 11434)│  │  (Port 8080)   │  │  /debug/llm  │
│                  │  │              │  │                │  │              │
│  Components:     │  │  Components: │  │  Components:   │  │  Components: │
│ • jenkins_client │  │ • llama2     │  │ • Master       │  │ • LLM status │
│ • build triggers │  │   model      │  │ • Executors    │  │ • Model list │
│ • status checks  │  │ • Native API │  │ • Jobs         │  │ • Ollama URL │
│ • log retrieval  │  │ • HTTP /api/ │  │ • Pipelines    │  │              │
└────────┬─────────┘  │   endpoints  │  │                │  └──────────────┘
         │            └──────────────┘  └────────────────┘
         │                  ▲
         │                  │ HTTP /api/generate
         │                  │ /v1/completions
         │                  │
         │            ┌─────┴──────────────┐
         │            │                    │
         │            │  Ollama-Puller     │
         │            │  (One-shot Job)    │
         │            │                    │
         │            │  - Waits for       │
         │            │    Ollama server   │
         │            │  - Pulls llama2    │
         │            │    model (~3.8GB)  │
         │            │  - Shared volume   │
         │            └────────────────────┘
         │
         │ XML-RPC (Jenkins integration)
         │
         ▼
    ┌─────────────────────────────────┐
    │    Jenkins Execution Layer       │
    │    (Docker Container)            │
    │                                  │
    │  - Build jobs execution          │
    │  - Pipeline management           │
    │  - Plugin system (workflow-job,  │
    │    workflow-cps, git)            │
    │  - Init scripts                  │
    │  - Persistent data volume        │
    └─────────────────────────────────┘

                    PERSISTENT STORAGE LAYER

    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ jenkins_data │  │ ollama_data  │  │ (Other vols) │
    │   volume     │  │   volume     │  │              │
    │              │  │              │  │              │
    │ ~/.jenkins/  │  │ ~/.ollama/   │  │              │
    │              │  │              │  │              │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## System Components

### 1. **Streamlit Web Interface** (Port 8501)
**File:** `streamlit/app.py`  
**Docker Image:** `python:3.10-slim` + Streamlit  

**Responsibilities:**
- Present interactive chat interface to end users
- Maintain message history in session state
- Send user queries to Agent via HTTP POST
- Parse and format Agent responses
- Display job lists, build confirmations, logs, and errors

**Key Features:**
```python
# Session management
st.session_state.messages  # Chat history

# User input
st.chat_input()            # Chat box

# Response formatting
st.markdown()              # Render responses
st.spinner()               # Loading indicator
st.chat_message()          # Role-based display
```

**Environment Variables:**
- `AGENT_URL`: Default `http://agent:8100/query`
- `FASTAPI_URL`: Default `http://fastapi:8000`

---

### 2. **Agent Service** (Port 8100)
**File:** `adk_agent/main.py` + `adk_agent/agent.py`  
**Docker Image:** Custom Python 3.10-slim with entrypoint wait script  

**Responsibilities:**
- Receive natural language queries via `/query` POST endpoint
- Route queries to appropriate handlers (LLM, Jenkins, status checks)
- Integrate with Ollama LLM for natural language understanding
- Orchestrate calls to FastAPI backend and Jenkins
- Return structured JSON responses

**Core Logic Flow:**

```
User Query
    ↓
Parse & Analyze (agent.py:run_agent())
    ↓
Keyword Detection:
├─ "list" → list_jenkins_jobs()
├─ "trigger"/"build" → trigger_jenkins_build()
├─ "status"/"check" → get_jenkins_status()
└─ (other) → call_llm()
    ↓
Generate Response
    ↓
Return JSON {"response": {...}, "success": true}
```

**Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query` | POST | Primary agent query handler |
| `/status/{job}/{build}` | GET | Get specific build status |
| `/logs/{job}/{build}` | GET | Get build logs |
| `/debug/llm` | GET | Debug LLM initialization & models |

**LLM Integration (agent.py):**

```python
# Initialization (lazy - happens on first query)
def init_llm():
    # Attempts OllamaLLM connection
    # Returns None if failed (allows retry)
    
# Call chain
def call_llm(prompt):
    1. Try LangChain OllamaLLM client
       ├─ llm.invoke()
       ├─ llm()
       └─ llm.generate()
    
    2. Fall back to HTTP endpoints:
       ├─ /api/generate
       ├─ /v1/completions
       ├─ /v1/chat/completions
       └─ /api/completions
    
    3. Try multiple payload formats
       ├─ {"model": "llama2", "prompt": "..."}
       ├─ {"model": "llama2", "messages": [...]}
       └─ {"model": "llama2", "input": "..."}
    
    4. Parse response
       ├─ Extract from "text" field
       ├─ Extract from "response" field
       ├─ Extract from "output" field
       └─ Extract from nested "choices"
```

**Environment Variables:**
- `OLLAMA_URL`: Default `http://ollama:11434`
- `FASTAPI_URL`: Default `http://fastapi:8000`

**Wait Mechanism:**
- Entrypoint: `adk_agent/wait-for-ollama-ready.sh`
- Polls Ollama HTTP endpoint until responsive
- Verifies llama2 model loaded via `/api/tags`
- Timeout: 120 retries (2-3s intervals) ≈ 5 minutes

---

### 3. **FastAPI Backend** (Port 8000)
**File:** `fast_api/main.py` + `fast_api/jenkins_client.py`  
**Docker Image:** Custom Python 3.10 with dependencies  

**Responsibilities:**
- Provide RESTful API wrapper around Jenkins
- Abstract Jenkins XML-RPC complexity
- Return standardized JSON responses
- Handle errors and edge cases

**Core Endpoints:**

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/` | GET | Health check | `{"status": "OK"}` |
| `/jobs` | GET | List all jobs | `{"jobs": [...], "count": N}` |
| `/build` | POST | Trigger build | `{"job": "...", "build_number": N}` |
| `/status/{job_name}/last` | GET | Last build status | `{"status": "SUCCESS/FAILED/..."}` |
| `/status/{job_name}/{build}` | GET | Specific build status | `{"status": "...", "duration": ms}` |
| `/logs/{job_name}/{build}` | GET | Build logs | `{"logs": "..."}` |

**Jenkins Integration (jenkins_client.py):**

```python
# Uses python-jenkins library for XML-RPC connection
jenkins_server = jenkins.Jenkins(JENKINS_URL, auth=(user, token))

# Operations:
├─ list_jobs() → Get all job names
├─ trigger_build(job_name) → Queue new build
├─ get_status(job, build_num) → Query build status
├─ get_last_status(job) → Last completed build
└─ get_logs(job, build_num) → Build console output
```

**Environment Variables:**
- `JENKINS_URL`: Default `http://jenkins:8080`
- `JENKINS_USER`: Default `admin`
- `JENKINS_TOKEN`: API token (from `.env`)

---

### 4. **Ollama LLM Service** (Port 11434)
**Image:** `ollama/ollama:latest`  

**Responsibilities:**
- Run Llama2 language model
- Provide HTTP API for text generation
- Persist model weights in Docker volume

**Key HTTP Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check (root endpoint) |
| `/api/tags` | GET | List loaded models |
| `/api/generate` | POST | Generate text (streaming) |
| `/v1/completions` | POST | OpenAI-compatible completions |
| `/v1/chat/completions` | POST | OpenAI-compatible chat endpoint |

**Model Details:**
- **Model:** Llama2 (7B parameters)
- **Size:** ~3.8 GB
- **License:** Llama Community License
- **Download Time:** 5-10 minutes (first run, depends on internet)

**Environment Variables:**
- `OLLAMA_HOST`: `0.0.0.0:11434` (Listen on all interfaces)
- `OLLAMA_DEBUG`: `0` (Production mode)

**Healthcheck:**
```yaml
test: ["CMD-SHELL", "curl -sS http://localhost:11434/ > /dev/null || exit 1"]
interval: 10s
timeout: 5s
retries: 20
start_period: 120s  # Give 2 minutes for server startup
```

---

### 5. **Ollama-Puller Service** (One-shot Job)
**Image:** `ollama/ollama:latest`  
**Type:** Service with `restart: "no"` (runs once)  

**Purpose:** Safely pull and cache the Llama2 model

**Execution Flow:**
```bash
1. Wait for Ollama server (max 120 seconds, 2s intervals)
2. Check if server responds to HTTP GET /
3. Once ready: Execute `ollama pull llama2`
4. Download model (~3.8 GB) to shared volume
5. Exit with status 0 (success)
```

**Exit Conditions:**
- ✅ Success: Model fully loaded → Service exits 0
- ✅ Already cached: Model file exists → Skip download, exit 0
- ❌ Timeout: Ollama not ready → Exit 1
- ❌ Network error: Can't reach download servers → Exit 1

**Depends On:**
```yaml
depends_on:
  - ollama  # Must start first
```

**Shared with:**
```yaml
volumes:
  - ollama_data:/root/.ollama  # Shared with Ollama service
```

---

### 6. **Jenkins CI/CD Master** (Port 8080, 50000)
**Image:** Custom `jenkins:lts` with plugins + init scripts  
**Dockerfile:** `Dockerfile` (root)  

**Responsibilities:**
- Execute build pipelines
- Manage job configurations
- Store build history and logs
- Provide XML-RPC API for remote control

**Installed Plugins:**
- `workflow-job` - Pipeline job support
- `workflow-cps` - Groovy DSL for pipelines
- `git` - Git repository integration

**Initialization:**

**Phase 1: Dockerfile Build**
```dockerfile
FROM jenkins/jenkins:lts
RUN apt-get install python3 python3-pip  # Agent requirements
RUN jenkins-plugin-cli --plugins workflow-job workflow-cps git
COPY scripts/init_jenkins.groovy /usr/share/jenkins/ref/init.groovy.d/001-init-security.groovy
```

**Phase 2: Container Startup**
- Jenkins starts in Docker
- Init scripts run automatically
- Creates admin user (if not exists)
- Configures security realm
- Disables setup wizard

**Phase 3: Job Initialization (`scripts/jenkins_init_jobs_fixed.py`)**
- Python script runs inside `jenkins-init` service
- Waits for Jenkins HTTP endpoint ready (curl loop)
- Reads Groovy pipeline files from repository
- Creates Jenkins pipeline jobs via Jenkins REST API
- Idempotent: Safe to run multiple times

**Persistent Storage:**
```yaml
volumes:
  - jenkins_data:/var/jenkins_home  # Shared with other services
```

---

## Data Flow

### Flow 1: User Asks Natural Language Question

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION                                              │
│    "What is Jenkins used for?"                                  │
│    Entered in Streamlit chat box                                │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 2. STREAMLIT → AGENT                                             │
│    POST http://agent:8100/query                                 │
│    Headers: Content-Type: application/json                      │
│    Body: {"prompt": "What is Jenkins used for?"}                │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 3. AGENT QUERY ROUTING (agent.py:run_agent())                   │
│    - Parse prompt_lower = "what is jenkins used for?"           │
│    - Check keywords: list/show/jobs? No                         │
│    - Check keywords: trigger/build/run? No                      │
│    - Check keywords: status/check? No                           │
│    → DEFAULT: Natural language query                            │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 4. LLM CALL (agent.py:call_llm())                               │
│    Attempt 1: LangChain OllamaLLM client                        │
│    Attempt 2: HTTP /api/generate                                │
│    Attempt 3: HTTP /v1/completions                              │
│    Attempt 4: HTTP /v1/chat/completions                         │
│                                                                   │
│    Makes POST to:                                               │
│    http://ollama:11434/api/generate                             │
│    Payload: {"model": "llama2", "prompt": "...", "stream": ...} │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 5. OLLAMA GENERATION                                             │
│    Llama2 processes prompt with system context                  │
│    Generates natural language response                          │
│    Returns: {"response": "Jenkins is an open-source...", ...}   │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 6. AGENT RESPONSE FORMATTING                                    │
│    Extract generated text                                       │
│    Wrap in JSON: {"response": {"message": "..."}, "success": T} │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 7. AGENT → STREAMLIT                                            │
│    HTTP 200 OK                                                  │
│    Body: {"response": {"message": "Jenkins is..."}, ...}        │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│ 8. STREAMLIT RENDERING                                          │
│    Parse response dict                                          │
│    Extract message field                                        │
│    Render with st.markdown() in chat interface                  │
│    Display to user                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 2: User Requests Job List

```
┌──────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                             │
│    "list jobs" OR "show me the jobs"                      │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 2. AGENT KEYWORD DETECTION                               │
│    prompt_lower contains "list" or "show" or "jobs"       │
│    → Trigger list_jenkins_jobs() path                     │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 3. AGENT → FASTAPI BACKEND                               │
│    GET http://fastapi:8000/jobs                          │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 4. FASTAPI → JENKINS                                     │
│    Calls jenkins_client.list_jobs()                      │
│    Uses python-jenkins XML-RPC connection                │
│    Jenkins Master (via port 8080)                        │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 5. JENKINS RESPONSE                                       │
│    Returns list of job names:                            │
│    ["build-api", "test-suite", "deploy-prod", ...]      │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 6. FASTAPI → AGENT                                       │
│    HTTP 200                                              │
│    {"success": true, "jobs": [...], "count": N}          │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 7. AGENT RESPONSE                                        │
│    {"response": {"jobs": [...]}, "success": true}        │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│ 8. STREAMLIT FORMATTING                                  │
│    Detects "jobs" key in response                        │
│    Renders as formatted markdown list:                  │
│    📋 **Available Jobs:**                                │
│    - `build-api`                                        │
│    - `test-suite`                                       │
│    - `deploy-prod`                                      │
└──────────────────────────────────────────────────────────┘
```

### Flow 3: User Triggers a Build

```
┌────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                          │
│    "trigger build-api" OR "run test-suite"            │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 2. AGENT KEYWORD DETECTION                             │
│    prompt contains "trigger" or "build" or "run"        │
│    → Extract job name from prompt                      │
│    → Fallback: fuzzy match against known jobs          │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 3. AGENT → FASTAPI                                     │
│    POST http://fastapi:8000/build                      │
│    Body: {"job_name": "build-api"}                     │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 4. FASTAPI → JENKINS                                   │
│    Calls jenkins_client.trigger_build("build-api")    │
│    Uses jenkins_server.build_job(name)                 │
│    Queues new build on next available executor         │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 5. JENKINS QUEUES BUILD                                │
│    Build assigned build_number (e.g., #42)             │
│    Returns build URL to FastAPI                        │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 6. FASTAPI RESPONSE                                    │
│    {"job": "build-api", "build_number": 42, ...}       │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 7. AGENT RESPONSE                                      │
│    Formats as confirmation:                            │
│    {"response": {"job": "build-api", "build": 42}, ..} │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 8. STREAMLIT DISPLAY                                   │
│    Shows build confirmation:                           │
│    "✅ Build triggered: build-api #42"                 │
└────────────────────────────────────────────────────────┘
```

---

## Technology Stack Details

### Backend Technologies

| Component | Purpose | Details |
|-----------|---------|---------|
| **FastAPI** | REST API framework | Python async, auto-docs (Swagger), type hints |
| **Pydantic** | Data validation | Request/response models with validation |
| **python-jenkins** | Jenkins client library | XML-RPC interface to Jenkins Master |
| **LangChain** | LLM framework | Abstracts Ollama LLM, provides invoke/generate interfaces |
| **Requests** | HTTP library | Makes direct calls to Ollama API (fallback) |

### Frontend Technologies

| Component | Purpose | Details |
|-----------|---------|---------|
| **Streamlit** | Web UI framework | Reactive, session-state-based, markdown rendering |
| **Python** | Runtime | 3.10-slim image for minimal footprint |

### LLM & ML Technologies

| Component | Purpose | Details |
|-----------|---------|---------|
| **Ollama** | LLM runtime | Docker-based, HTTP API, model management |
| **Llama2** | Language model | Meta's open-source 7B parameter model |
| **LangChain** | LLM integration | Provides OllamaLLM class with invoke/generate |

### DevOps & Infrastructure

| Component | Purpose | Details |
|-----------|---------|---------|
| **Docker** | Containerization | Each service in isolated container |
| **Docker Compose** | Orchestration | Multi-container coordination, volumes, networking |
| **Jenkins** | CI/CD server | Build automation, pipeline execution, artifact storage |
| **Bash** | Scripting | Entrypoint wait scripts, service initialization |

### Architecture Patterns

| Pattern | Implementation |
|---------|----------------|
| **Microservices** | Separate containers for agent, API, UI, Jenkins, Ollama |
| **API Gateway** | Agent acts as orchestrator between UI and backend services |
| **Async/Await** | FastAPI uses async for non-blocking I/O |
| **Lazy Loading** | LLM initialized on first use, not at startup |
| **Circuit Breaker** | Multiple fallback endpoints for LLM calls |
| **Dependency Injection** | Environment variables for service discovery |

---

## Deployment & Orchestration

### Docker Compose Configuration

**File:** `docker-compose.yml` (Version 3.8)

**Services Defined:**

```yaml
services:
  jenkins:          # CI/CD Master
  jenkins-init:     # Job initialization utility
  fastapi:          # Backend API
  ollama:           # LLM Server
  ollama-puller:    # Model cache job
  agent:            # Orchestration service
  streamlit:        # Web UI

volumes:
  jenkins_data:     # Jenkins configuration & build history
  ollama_data:      # Model weights & cache
  agent:            # (Optional) Agent working directory
  fastapi:          # (Optional) API working directory
```

### Startup Orchestration

```
┌─ Parallel Start (no dependencies)
├─ Jenkins
├─ Ollama (server)
└─ FastAPI

┌─ Sequential Dependencies
├─ Jenkins-init (waits for Jenkins ready)
├─ Ollama-puller (waits for Ollama server ready)
└─ Agent (waits for Ollama-puller to complete successfully)
    └─ Streamlit (waits for Agent ready)
```

**Dependency Chain:**
```yaml
agent:
  depends_on:
    fastapi:
      condition: service_started
    ollama:
      condition: service_started
    ollama-puller:
      condition: service_completed_successfully  # Critical!

streamlit:
  depends_on:
    agent:
      condition: service_started
    fastapi:
      condition: service_started
```

### Environment Variables

**.env file:**
```bash
JENKINS_URL=http://jenkins:8080
JENKINS_USER=admin
JENKINS_TOKEN=<api-token>
```

**Docker Compose Environment:**
```yaml
# Agent service
environment:
  - FASTAPI_URL=http://fastapi:8000
  - OLLAMA_URL=http://ollama:11434

# Streamlit service
environment:
  - AGENT_URL=http://agent:8100/query
  - FASTAPI_URL=http://fastapi:8000

# Ollama service
environment:
  - OLLAMA_HOST=0.0.0.0:11434
  - OLLAMA_DEBUG=0
```

### Health Checks

```yaml
ollama:
  healthcheck:
    test: ["CMD-SHELL", "curl -sS http://localhost:11434/ > /dev/null || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 20
    start_period: 120s
```

---

## API Specifications

### Agent API (Port 8100)

#### POST /query
**Purpose:** Primary endpoint for natural language queries

**Request:**
```json
{
  "prompt": "list jobs"
}
```

**Response (Success):**
```json
{
  "response": {
    "jobs": ["job-1", "job-2"],
    "message": "Here are the available jobs..."
  },
  "success": true
}
```

**Response (Natural Language):**
```json
{
  "response": {
    "message": "Jenkins is a powerful open-source automation server..."
  },
  "success": true
}
```

#### GET /debug/llm
**Purpose:** Inspect LLM status and available models

**Response:**
```json
{
  "llm_initialized": true,
  "models": "[{\"name\": \"llama2:latest\", \"model\": \"llama2\", ...}]",
  "ollama_url": "http://ollama:11434"
}
```

### FastAPI Backend (Port 8000)

#### GET /jobs
```json
{
  "success": true,
  "jobs": ["build-api", "test-suite", "deploy-prod"],
  "count": 3
}
```

#### POST /build
```json
{
  "success": true,
  "job": "build-api",
  "build_number": 42,
  "status": "queued"
}
```

#### GET /status/{job_name}/{build_number}
```json
{
  "success": true,
  "job": "build-api",
  "build_number": 42,
  "status": "SUCCESS",
  "duration": 145000
}
```

#### GET /logs/{job_name}/{build_number}
```json
{
  "success": true,
  "job": "build-api",
  "build_number": 42,
  "logs": "[...] build output here ..."
}
```

### Ollama API (Port 11434)

#### GET /api/tags
```json
{
  "models": [
    {
      "name": "llama2:latest",
      "modified_at": "2024-04-20T...",
      "size": 3825922048
    }
  ]
}
```

#### POST /api/generate
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "What is Jenkins?",
    "stream": false
  }'

# Response:
{
  "response": "Jenkins is an open-source automation server...",
  "context": [...],
  "done": true
}
```

---

## LLM Integration

### Llama2 Model Details

**Model:** Llama2 (Meta)  
**Parameters:** 7 Billion  
**Training Data:** 2 Trillion tokens  
**License:** Llama Community License  
**Size:** ~3.8 GB  
**Context Window:** 4096 tokens  
**Architecture:** Transformer-based decoder-only  

**Capabilities:**
- Natural language understanding
- Code generation
- Question answering
- Text summarization
- Instruction following

### Integration Architecture

```
Agent (Python)
    ↓
Two-tier Integration:
    ├─ Layer 1: LangChain OllamaLLM (Python object)
    │   ├─ llm.invoke(prompt)         # Most efficient
    │   ├─ llm(prompt)                # Callable interface
    │   └─ llm.generate(prompt)       # Batch generation
    │
    └─ Layer 2: Direct HTTP API (Fallback)
        ├─ /api/generate              # Native Ollama endpoint
        ├─ /v1/completions            # OpenAI-compatible
        ├─ /v1/chat/completions       # Chat format
        └─ /api/completions           # Alternative

Response Parsing:
    ├─ Extract text field
    ├─ Extract response field
    ├─ Extract output field
    ├─ Extract from nested choices
    └─ Return raw response text if all fail
```

### System Prompt

```python
SYSTEM_PROMPT = """You are a helpful assistant for Jenkins CI/CD automation.
You have access to Jenkins jobs and build management capabilities.

You can help users:
- Understand what Jenkins is and how it works
- Manage build jobs
- Check build status
- View build logs

Be helpful, conversational, and provide clear explanations."""
```

### Response Extraction Logic

```python
def extract_response(json_response):
    # Try multiple keys in order
    for key in ("text", "response", "output", "result", "completion", "data", "message"):
        if key in json_response and isinstance(json_response[key], str):
            return json_response[key]
    
    # Check nested structures
    if "choices" in json_response and len(json_response["choices"]) > 0:
        choice = json_response["choices"][0]
        if "message" in choice:
            return choice["message"].get("content", "")
        if "text" in choice:
            return choice["text"]
    
    # Fallback: return whole response
    return str(json_response)
```

---

## Security & Configuration

### Authentication & Authorization

**Jenkins:**
- Admin user created via Groovy init script
- API token generated for programmatic access
- Stored in `.env` file (not committed)

**Services:**
- No inter-service authentication
- Assumes Docker internal network security
- Should be updated for production with mTLS or OAuth

### Credential Management

**.env File (NEVER COMMIT):**
```bash
JENKINS_URL=http://jenkins:8080
JENKINS_USER=admin
JENKINS_TOKEN=<generated-token>
```

**Secret Handling:**
```python
import os

JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "")  # From .env or environment
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
```

### Network Isolation

**Docker Compose Default Network:**
- All services on `<project>_default` bridge network
- Services accessible by hostname (e.g., `http://ollama:11434`)
- Externally exposed only on published ports

**Published Ports:**
```yaml
ports:
  - "8501:8501"   # Streamlit (UI)
  - "8100:8100"   # Agent
  - "8000:8000"   # FastAPI
  - "8080:8080"   # Jenkins Web UI
  - "50000:50000" # Jenkins agent communication
  - "11434:11434" # Ollama (optional, for external tools)
```

### Production Considerations

- [ ] Add reverse proxy (nginx) with TLS
- [ ] Implement API authentication (JWT/OAuth)
- [ ] Use secrets management system (Vault, AWS Secrets Manager)
- [ ] Enable Jenkins security realm (LDAP, SAML)
- [ ] Add request rate limiting
- [ ] Implement audit logging
- [ ] Use Kubernetes instead of Docker Compose
- [ ] Add monitoring & alerting (Prometheus, Grafana)
- [ ] Enable container image scanning
- [ ] Implement CI/CD for the CI/CD tool itself

---

## Troubleshooting Guide

### Issue: Agent Returns Default Message Instead of LLM Response

**Symptoms:**
```
"I can help you with Jenkins automation. Try commands like..."
```

**Root Causes:**
1. Ollama not running or model not loaded
2. LLM initialization failed
3. All HTTP endpoints returning errors

**Diagnosis:**
```bash
# Check Ollama is running
docker-compose ps ollama

# Check model is loaded
docker-compose exec ollama ollama list

# Check HTTP connectivity
curl http://localhost:11434/api/tags

# Check agent logs
docker-compose logs agent --tail=100 | grep -i "llm\|ollama\|error"
```

**Solutions:**
```bash
# Restart Ollama
docker-compose restart ollama ollama-puller

# Check wait script logs
docker-compose logs ollama-puller --tail=50

# Verify model size & download time
# Llama2: ~3.8 GB = 5-15 minutes on typical internet

# Force rebuild
docker-compose down -v
docker-compose up -d --build
```

### Issue: Agent Won't Start / Timeout Waiting for Ollama

**Symptoms:**
```
Agent container continuously restarting
docker-compose logs agent shows timeout errors
```

**Root Causes:**
1. Ollama server not responding
2. Wait script timeout too short
3. Model too large for disk space

**Diagnosis:**
```bash
# Check Ollama logs
docker-compose logs ollama --tail=100

# Check disk space
docker system df

# Check ollama-puller progress
docker-compose logs ollama-puller
```

**Solutions:**
```bash
# Increase wait timeout in wait-for-ollama-ready.sh
MAX_RETRIES=180  # From 120

# Free up disk space
docker system prune -a --volumes

# Check internet connectivity
docker-compose exec ollama ping 8.8.8.8
```

### Issue: Jenkins Jobs Won't List or Trigger Fails

**Symptoms:**
```json
{
  "error": "Failed to list jobs"
}
```

**Root Causes:**
1. Jenkins not fully initialized
2. API token invalid/expired
3. Network connectivity between services

**Diagnosis:**
```bash
# Check Jenkins is running
docker-compose ps jenkins

# Check Jenkins logs
docker-compose logs jenkins --tail=100

# Test Jenkins API manually
curl -u admin:<token> http://localhost:8080/api/json

# Check FastAPI service
docker-compose logs fastapi --tail=50
```

**Solutions:**
```bash
# Reinitialize Jenkins
docker-compose restart jenkins jenkins-init

# Generate new API token
# Go to Jenkins UI (8080) → Manage Jenkins → API Token

# Update .env
JENKINS_TOKEN=<new-token>

# Restart services
docker-compose restart agent fastapi
```

### Issue: Streamlit UI Shows Connection Error

**Symptoms:**
```
"Unable to connect to Agent service"
```

**Root Causes:**
1. Agent service not running
2. Port 8100 not exposed
3. Streamlit environment variable incorrect

**Diagnosis:**
```bash
# Check services running
docker-compose ps

# Check port is open
netstat -an | grep 8100
curl http://localhost:8100/

# Check Streamlit logs
docker-compose logs streamlit --tail=100
```

**Solutions:**
```bash
# Start all services
docker-compose up -d

# Wait for Ollama-puller to complete
sleep 300

# Check Streamlit can reach Agent
docker-compose exec streamlit curl http://agent:8100/
```

### Issue: LLM Responses Are Slow

**Causes:**
- Llama2 inference is CPU-intensive
- First request includes model loading
- Network latency to Ollama

**Solutions:**
```bash
# Use GPU if available (update docker-compose.yml)
ollama:
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all

# Reduce response length in system prompt
# Add: "Keep responses under 100 words"

# Pre-warm model with test request
docker-compose exec ollama ollama generate llama2 "test"
```

### Issue: Model Download Fails / Stuck

**Symptoms:**
```
ollama-puller logs show: "pull failed" or timeout
```

**Root Causes:**
- Network connectivity issues
- Download server unreachable
- Insufficient disk space
- Timeout too short

**Solutions:**
```bash
# Increase retry timeout
docker-compose down -v
# Edit docker-compose.yml: ollama-puller sleep intervals

# Try manual pull
docker-compose exec ollama ollama pull llama2

# Check network
docker-compose exec ollama curl -I https://registry.ollama.ai/

# Increase disk space (Docker Desktop settings)

# Use alternative model
# Edit docker-compose.yml: ollama pull mistral
# Edit adk_agent/agent.py: model="mistral"
```

---

## File Structure Reference

```
project-root/
├── docker-compose.yml           # Main orchestration
├── .env                         # Secrets (gitignored)
├── Dockerfile                   # Jenkins builder
│
├── adk_agent/                   # Agent service
│   ├── main.py                  # FastAPI app
│   ├── agent.py                 # Core orchestration logic
│   ├── Dockerfile               # Agent image
│   ├── requirements.txt          # Python dependencies
│   ├── wait-for-ollama-ready.sh # Entrypoint startup script
│   └── __init__.py
│
├── fast_api/                    # Backend API service
│   ├── main.py                  # FastAPI REST API
│   ├── jenkins_client.py        # Jenkins integration
│   ├── Dockerfile               # API image
│   ├── requirements.txt
│   └── __init__.py
│
├── streamlit/                   # Frontend UI service
│   ├── app.py                   # Streamlit chat app
│   ├── Dockerfile               # UI image
│   └── requirements.txt
│
├── Jenkins/                     # Jenkins configuration (persistent)
│   └── init.groovy.d/           # Groovy init scripts
│       └── 001-init-security.groovy
│
├── jenkins_init_jobs_fixed.py   # Job initialization script
└── *.groovy                     # Pipeline definitions
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Clone repository
- [ ] Create `.env` with Jenkins token
- [ ] Ensure Docker & Docker Compose installed
- [ ] Verify disk space (≥20 GB recommended)
- [ ] Check internet connection (for model download)

### Deployment
- [ ] Run `docker-compose build --no-cache`
- [ ] Run `docker-compose up -d`
- [ ] Monitor logs: `docker-compose logs -f ollama-puller`
- [ ] Wait for model download (5-15 minutes)

### Post-Deployment
- [ ] Access Streamlit: `http://localhost:8501`
- [ ] Test query: "list jobs"
- [ ] Verify Jenkins: `http://localhost:8080`
- [ ] Check LLM: `curl http://localhost:8100/debug/llm`

### Testing
- [ ] Natural language query: "What is Jenkins?"
- [ ] Job listing: "show me all jobs"
- [ ] Build trigger: "run build-api"
- [ ] Status check: "check status of my-job"

---

## Conclusion

This architecture provides a production-ready foundation for conversational CI/CD automation. The modular design allows independent scaling of components, and multiple fallback mechanisms ensure resilience. Future enhancements could include:

- Multi-model support (swap Llama2 for other models)
- Advanced authentication & authorization
- Persistent conversation history
- Build failure notifications
- Integration with more DevOps tools (Terraform, Kubernetes, etc.)
- Performance optimization with caching
- Advanced monitoring & observability

---

**Document Version:** 2.0  
**Last Updated:** April 20, 2026  
**Maintained By:** Agentic AI DevOps Team  
**License:** Project License
