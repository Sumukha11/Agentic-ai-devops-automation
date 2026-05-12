# Ollama Startup Fix Guide

## Changes Made

The docker-compose.yml has been fixed with the following improvements:

### 1. **Ollama Service Enhancements**
   - Added `OLLAMA_HOST=0.0.0.0:11434` to ensure proper network binding
   - Improved healthcheck with `CMD-SHELL` format and longer startup period (120s)
   - Extended retry count to 20 to handle slow startups
   - Added `OLLAMA_DEBUG=0` environment variable

### 2. **ollama-puller Service Fixes**
   - Fixed entrypoint with proper bash syntax (removed double-dollar escaping issues)
   - Added retry logic with proper variable handling
   - Increased retry timeout from 60s to 120s to handle server startup delays
   - Simplified variable syntax to avoid composition variable interpolation warnings

### 3. **Version Update**
   - Updated docker-compose version to '3.8' for better compatibility

## How to Run

1. **Stop existing containers:**
   ```bash
   cd c:\Users\rampr\OneDrive\Desktop\IITP-3rd-sem-project-Agentic_AI_DevOps_Tools
   docker-compose down -v
   ```

2. **Clean up volumes (if persistent issues):**
   ```bash
   docker volume rm iitp-3rd-sem-project-agentic_ai_devops_tools_ollama_data
   ```

3. **Build and start the stack:**
   ```bash
   docker-compose up -d --build
   ```

4. **Monitor the Ollama startup:**
   ```bash
   docker-compose logs -f ollama --tail=50
   ```

5. **Monitor the ollama-puller (model download):**
   ```bash
   docker-compose logs -f ollama-puller --tail=50
   ```

## Verification Steps

Once containers are running:

1. **Check Ollama is responding:**
   ```bash
   curl http://localhost:11434/
   ```

2. **Check if mistral model was pulled:**
   ```bash
   docker-compose exec ollama ollama list
   ```

3. **Check agent can access Ollama:**
   ```bash
   curl -sS http://localhost:8100/debug/llm | findstr /i ollama
   ```

4. **Test a query:**
   ```bash
   curl -X POST http://localhost:8100/query -H "Content-Type: application/json" -d "{\"prompt\":\"Hello\"}"
   ```

## Troubleshooting

### If Ollama still won't start:

1. **Check port conflicts:**
   ```bash
   netstat -ano | findstr :11434
   ```

2. **Force remove orphaned containers:**
   ```bash
   docker-compose down --remove-orphans
   docker system prune -a --volumes
   ```

3. **Check Docker daemon:**
   ```bash
   docker info
   docker ps
   ```

### If model pull fails:

1. **Check Ollama logs:**
   ```bash
   docker-compose logs ollama --tail=100
   ```

2. **Check puller logs:**
   ```bash
   docker-compose logs ollama-puller --tail=100
   ```

3. **Try pulling manually:**
   ```bash
   docker-compose exec ollama ollama pull mistral
   ```

## Expected Timeline

- Ollama server startup: 10-30 seconds
- Mistral model pull: 2-10 minutes (first time, depends on internet speed)
- Full stack ready: 3-15 minutes
