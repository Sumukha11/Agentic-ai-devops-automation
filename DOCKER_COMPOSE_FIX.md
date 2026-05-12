# Docker Compose Fix - Variable Escaping & ollama-puller Error

## Issue Summary

When running `docker-compose up -d --build`, you encountered:

```
WARN[0000] The "retry_count" variable is not set. Defaulting to a blank string.
WARN[0000] The "max_retries" variable is not set. Defaulting to a blank string.
WARN[0000] version attribute is obsolete
✘ Container ollama-puller service "ollama-puller" didn't complete successfully: exit 1
```

## Root Cause

**Variable Interpolation Problem:**
- Docker Compose was interpreting `$retry_count` and `$max_retries` as Compose environment variables
- These weren't defined, so they became empty strings
- This caused the bash script to have syntax errors: `[ -ge 60 ]` (missing variable)
- Ollama-puller service failed with exit code 1

**Version Deprecation:**
- Docker Compose v2+ deprecates the `version` field
- While not breaking, it causes unnecessary warnings

## Solutions Applied

### 1. Fixed Variable Escaping in docker-compose.yml

**Changed FROM:**
```yaml
entrypoint: >
  /bin/bash -c "
  ...
  if [ $retry_count -ge $max_retries ]; then
    ...
  fi
  retry_count=$((retry_count + 1))
  ...
  "
```

**Changed TO:**
```yaml
entrypoint: >
  /bin/bash -c "
  ...
  if [ $$retry_count -ge $$max_retries ]; then
    ...
  fi
  retry_count=$$(( $$retry_count + 1 ))
  ...
  "
```

**Explanation:**
- In Docker Compose YAML, `$$` is an escape sequence for `$`
- Docker Compose processes `$$` and converts it to single `$`
- Single `$` then passes to bash for variable substitution
- So `$$retry_count` → becomes `$retry_count` in bash → evaluated by bash

### 2. Removed Obsolete Version Attribute

**Changed FROM:**
```yaml
version: '3.8'

services:
```

**Changed TO:**
```yaml
services:
```

## How to Deploy with Fixes

```bash
cd /mnt/c/Users/rampr/OneDrive/Desktop/IITP-3rd-sem-project-Agentic_AI_DevOps_Tools

# Remove old containers (if any)
docker-compose down -v

# Rebuild and start with fixed config
docker-compose up -d --build

# Watch ollama-puller logs (should complete successfully now)
docker-compose logs ollama-puller --tail=50

# After model loads, check status
docker-compose ps

# Verify model is loaded
docker-compose exec ollama ollama list
```

## What the Fixed Script Does

The corrected ollama-puller entrypoint:

```bash
#!/bin/bash

echo 'Waiting for Ollama server...'
max_retries=60                    # Set retry limit
retry_count=0                     # Initialize counter

# Poll Ollama HTTP endpoint
while ! curl -sS http://ollama:11434/ >/dev/null 2>&1; do
    if [ $$retry_count -ge $$max_retries ]; then  # Compare properly now
        echo 'Ollama server did not start in time'
        exit 1
    fi
    retry_count=$$(( $$retry_count + 1 ))  # Increment counter properly
    sleep 2
done

echo 'Ollama server is ready'
echo 'Pulling llama2 model...'

ollama pull llama2  # This may take 5-15 minutes

echo 'Llama2 model pulled successfully'
```

## Expected Behavior After Fix

```
✔ Container ollama                                    Started
✔ Container jenkins                                   Started
✔ Container fastapi                                   Started
✔ Container ollama-puller                             Completed Successfully ✓
✔ Container agent                                     Started
✔ Container streamlit                                 Started
```

**Timeline:**
1. **0-10s:** Ollama starts, jenkins/fastapi initialize
2. **10-30s:** ollama-puller waits for Ollama HTTP endpoint
3. **30-120s:** Ollama server becomes ready
4. **120-600s:** Llama2 model downloads (~3.8 GB)
5. **600s+:** Agent starts (waits for ollama-puller success)
6. **600s+:** Streamlit starts (waits for agent ready)

## Troubleshooting

### If ollama-puller still fails:

```bash
# Check ollama-puller logs in detail
docker-compose logs ollama-puller --tail=100

# Manually check if Ollama is responding
docker-compose exec ollama curl http://localhost:11434/

# Check disk space (model is 3.8 GB)
docker system df

# Try manual pull
docker-compose exec ollama ollama pull llama2
```

### If you see "connection refused":
- Wait longer for Ollama to fully start (2-3 minutes)
- Check: `docker-compose logs ollama --tail=50`

### If model download times out:
- Increase `max_retries` in ollama-puller entrypoint (e.g., 300 for 10 minutes)
- Check internet connectivity: `docker-compose exec ollama ping 8.8.8.8`
- Check disk space

## Files Modified

- **docker-compose.yml**
  - Removed `version: '3.8'` field (obsolete)
  - Fixed ollama-puller entrypoint (escaped `$` as `$$`)

## Summary

✅ Docker Compose YAML parsing fixed  
✅ Bash variable interpolation corrected  
✅ ollama-puller should now complete successfully  
✅ No more "variable not set" warnings  
✅ Model pull can proceed without script errors  

Run `docker-compose up -d --build` again - it should work!
