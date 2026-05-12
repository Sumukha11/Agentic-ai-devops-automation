# Ollama-Puller Fix - Final Version

## What Changed

The ollama-puller service entrypoint has been simplified to:

1. **Use a for-loop instead of while** (more reliable for counting)
2. **Remove the variable assignment issues** (simpler bash syntax)
3. **Check if model already exists** before pulling (avoid redundant downloads)
4. **Explicit exit 0 on success** (ensures service_completed_successfully status)
5. **Better logging** with [ollama-puller] prefix for clarity

## Key Improvements

```bash
# OLD (had issues with variable escaping):
while ! curl ... ; do
  if [ $$retry_count -ge $$max_retries ]; then
    ...
  fi
  retry_count=$$(( $$retry_count + 1 ))
done

# NEW (simpler, more reliable):
for i in {1..120}; do
  if curl ... ; then
    break
  fi
  if [ $$i -eq 120 ]; then
    exit 1
  fi
done
```

## How to Run

```bash
# Clean up old containers
docker-compose down -v

# Rebuild and start
docker-compose up -d --build

# Watch ollama-puller progress (real-time)
docker-compose logs -f ollama-puller

# Expected output:
# [ollama-puller] Waiting for Ollama server...
# [ollama-puller] ✓ Ollama server is ready
# [ollama-puller] Checking for llama2 model...
# [ollama-puller] Pulling llama2 model (this may take 5-15 minutes)...
# (model downloads)
# [ollama-puller] ✓ Model pull complete
```

## Timeline

- **0-2min:** Ollama starts
- **2-3min:** ollama-puller waits for Ollama HTTP endpoint
- **3-5min:** Ollama server fully ready
- **5-20min:** Llama2 model downloads (~3.8 GB, depends on internet)
- **20min+:** Agent starts, then Streamlit

## If Still Failing

Check the detailed logs:

```bash
# Full ollama-puller logs
docker-compose logs ollama-puller --tail=200

# Check if Ollama server is running
docker-compose ps ollama

# Manually test connectivity
docker-compose exec ollama curl http://localhost:11434/

# Check disk space (need ~5 GB free)
docker system df
```

## Success Indicator

All services should show ✓ (not ✘):

```
✔ ollama                Started
✔ ollama-puller         Exited successfully (exit code 0)
✔ agent                 Started
✔ streamlit             Started
```
