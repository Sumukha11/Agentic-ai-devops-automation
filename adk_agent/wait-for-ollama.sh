#!/bin/sh
# Wait for Ollama server and optionally for a model to appear. Exits 0 on success or timeout
OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
MODEL=${OLLAMA_MODEL:-mistral}
TIMEOUT=${WAIT_TIMEOUT:-300}
INTERVAL=${WAIT_INTERVAL:-2}

echo "Waiting for Ollama at $OLLAMA_URL (timeout=${TIMEOUT}s)"
end=$((SECONDS+TIMEOUT))
while [ $SECONDS -le $end ]; do
  if curl -sS "$OLLAMA_URL/" >/dev/null 2>&1; then
    echo "Ollama server reachable"
    if curl -sS "$OLLAMA_URL/api/models" | grep -q "$MODEL"; then
      echo "Model $MODEL available"
      exit 0
    else
      echo "Model $MODEL not present yet"
    fi
  fi
  sleep $INTERVAL
done

echo "Timed out waiting for model $MODEL"
exit 1
