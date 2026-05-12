FROM python:3.10-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && apt-get clean

COPY adk_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy wait script
COPY adk_agent/wait-for-ollama-ready.sh /app/wait-for-ollama-ready.sh
RUN chmod +x /app/wait-for-ollama-ready.sh

# Copy application files
COPY . .

EXPOSE 8100

# Use entrypoint to wait for Ollama before starting uvicorn
ENTRYPOINT ["/app/wait-for-ollama-ready.sh"]
CMD ["uvicorn", "adk_agent.main:app", "--host", "0.0.0.0", "--port", "8100"]