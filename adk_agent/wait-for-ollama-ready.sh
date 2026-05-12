#!/bin/bash
# Wait for Ollama service to be fully ready with model loaded

set -e

OLLAMA_URL="${OLLAMA_URL:-http://ollama:11434}"
MODEL_NAME="${OLLAMA_MODEL:-llama3}"

MAX_RETRIES=120
RETRY_COUNT=0

echo "⏳ Waiting for Ollama to be ready at $OLLAMA_URL..."

# Wait for Ollama HTTP endpoint
while ! curl -sS "$OLLAMA_URL/api/tags" > /dev/null 2>&1; do

    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Ollama server did not start within timeout"
        exit 1
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))

    echo "  [$RETRY_COUNT/$MAX_RETRIES] Waiting for Ollama server..."

    sleep 2
done

echo "✅ Ollama server is responding"

# Wait for model to exist
RETRY_COUNT=0

while true; do

    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ $MODEL_NAME model not found within timeout"
        exit 1
    fi

    MODEL_CHECK=$(curl -sS "$OLLAMA_URL/api/tags" 2>/dev/null)

    if echo "$MODEL_CHECK" | grep -q "$MODEL_NAME"; then
        echo "✅ $MODEL_NAME model is loaded and ready"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))

    echo "  [$RETRY_COUNT/$MAX_RETRIES] Waiting for $MODEL_NAME model to load..."

    sleep 3
done

echo "✅ Ollama is fully ready!"

exec "$@"