FROM python:3.10-slim

WORKDIR /app

# Install Terraform directly from HashiCorp release binaries
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip ca-certificates && \
    curl -fsSLo /tmp/terraform.zip https://releases.hashicorp.com/terraform/1.6.3/terraform_1.6.3_linux_amd64.zip && \
    unzip -o /tmp/terraform.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/terraform && \
    rm -f /tmp/terraform.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

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