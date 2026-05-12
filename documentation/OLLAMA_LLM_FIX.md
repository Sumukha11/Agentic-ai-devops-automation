# Ollama LLM Integration Fix

## Problem Identified

The agent was returning hardcoded default responses instead of using Ollama for natural language generation because:

1. **LLM initialization happened only once at startup**, before the model was loaded
2. **The `if llm:` guard prevented HTTP fallback** when LLM client was None
3. **Agent depends_on used `service_started`**, not waiting for model to actually load
4. **No retry mechanism** if Ollama wasn't ready on first check

## Solution Implemented

### 1. **Agent Code (adk_agent/agent.py)**
   - ✅ Removed `if llm:` guard in run_agent() 
   - ✅ **Always attempt LLM calls** for non-keyword queries
   - ✅ Improved `init_llm()` to allow retries (returns None on failure instead of setting global)
   - ✅ Enhanced `call_llm()` with:
     - Multiple HTTP endpoint variants (`/api/generate`, `/v1/completions`, `/v1/chat/completions`)
     - Multiple payload format attempts
     - Better response parsing (extracts from various JSON structures)
     - Detailed logging of all attempts

### 2. **Agent Dockerfile (adk_agent/Dockerfile)**
   - ✅ Added curl installation for health checks
   - ✅ Created new wait script that verifies Ollama is READY
   - ✅ Set entrypoint to wait-for-ollama-ready.sh (waits before starting uvicorn)

### 3. **Wait Script (adk_agent/wait-for-ollama-ready.sh)**
   - ✅ Polls Ollama HTTP endpoint until responsive
   - ✅ Checks `/api/tags` to verify mistral model is loaded
   - ✅ Timeout logic (120 retries, 2-3 second intervals = ~4-6 minutes max)
   - ✅ Allows proceeding if server is up (model may load in background)

### 4. **Docker Compose (docker-compose.yml)**
   - ✅ Added agent depends_on: `ollama-puller: service_completed_successfully`
   - ✅ Ensures model is fully pulled before agent starts
   - ✅ Removed hardcoded command (uses Dockerfile entrypoint/CMD instead)

## How It Works Now

1. **Ollama starts** → runs `/api/generate` endpoint
2. **ollama-puller service runs** → waits for Ollama, pulls mistral model (~2-5 minutes)
3. **Agent starts** → runs wait-for-ollama-ready.sh → polls `/api/tags` until mistral is present
4. **Agent runs uvicorn** → ready to receive queries
5. **User sends query** → Agent attempts call_llm() with:
   - LangChain client (if initialized)
   - Direct HTTP calls to multiple Ollama endpoints
   - Proper response parsing
6. **LLM response returned** → Displayed to user in natural language

## Testing Instructions

### 1. Clean and build fresh stack:
```bash
cd "c:\Users\rampr\OneDrive\Desktop\IITP-3rd-sem-project-Agentic_AI_DevOps_Tools"
docker-compose down -v
docker-compose up -d --build
```

### 2. Watch the startup sequence:
```bash
# Terminal 1: Watch Ollama
docker-compose logs -f ollama --tail=50

# Terminal 2: Watch ollama-puller (model download)
docker-compose logs -f ollama-puller --tail=50

# Terminal 3: Watch agent startup
docker-compose logs -f agent --tail=50
```

### 3. Verify Ollama is ready:
```bash
docker-compose exec ollama ollama list
# Should show: NAME                     ID              SIZE    MODIFIED
#             mistral:latest           ...             ...     ...
```

### 4. Test agent with natural language:
```bash
curl -X POST http://localhost:8100/query \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is Jenkins used for?"}' | jq
```

**Expected response:** Natural language answer from Mistral, NOT the hardcoded message

### 5. Check LLM debug endpoint:
```bash
curl -sS http://localhost:8100/debug/llm | jq
```

## Expected Output

When working correctly, you should see:
1. Agent logs: `🤖 Attempting LLM call for natural language query...`
2. Then: `✅ LLM response via langchain invoke` (or HTTP variant)
3. Response contains natural language from Ollama, e.g.: 
   ```
   "Jenkins is an open-source automation server commonly used for..."
   ```

NOT:
```
"I can help you with Jenkins automation. Try commands like..."
```

## Troubleshooting

### Agent returns default message:
1. Check agent logs: `docker-compose logs agent --tail=100`
2. Verify Ollama running: `docker-compose ps ollama`
3. Verify model loaded: `docker-compose exec ollama ollama list | grep mistral`
4. Test Ollama directly: `curl http://localhost:11434/api/tags`

### Model not loading:
1. Check ollama-puller logs: `docker-compose logs ollama-puller`
2. Try manual pull: `docker-compose exec ollama ollama pull mistral`
3. Check disk space: `docker system df`
4. Check internet connection: `docker-compose exec ollama ping 8.8.8.8`

### Agent won't start:
1. Check wait script: `docker-compose logs agent --tail=100 | grep -E "Waiting|Error|Timeout"`
2. Verify Ollama endpoint: `curl http://localhost:11434/`
3. Try rebuild: `docker-compose up -d --build --force-recreate agent`
