#!/bin/bash
set -e

echo "Starting Ollama initialization..."

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 5

# Try to pull mistral model (retry logic)
for i in {1..10}; do
  echo "Attempt $i to pull mistral model..."
  if ollama pull mistral; then
    echo "Successfully pulled mistral model"
    break
  else
    echo "Pull attempt $i failed, retrying in 5 seconds..."
    sleep 5
  fi
done

# Keep Ollama running in foreground
wait $OLLAMA_PID
