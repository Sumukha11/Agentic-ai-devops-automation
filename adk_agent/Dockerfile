FROM python:3.10-slim

WORKDIR /app

# Install Terraform, Kind, and kubectl for AI-managed local Kubernetes deployments
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip ca-certificates && \
    curl -fsSLo /tmp/terraform.zip https://releases.hashicorp.com/terraform/1.6.3/terraform_1.6.3_linux_amd64.zip && \
    unzip -o /tmp/terraform.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/terraform && \
    curl -fsSLo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && \
    chmod +x /usr/local/bin/kind && \
    curl -fsSLo /usr/local/bin/kubectl https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    rm -f /tmp/terraform.zip && \
    curl -fsSLo /tmp/docker.tgz https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz && \
    tar xzf /tmp/docker.tgz --strip-components=1 -C /usr/local/bin && \
    rm -f /tmp/docker.tgz && \
    mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -fsSLo /usr/local/lib/docker/cli-plugins/docker-compose https://github.com/docker/compose/releases/download/v2.30.3/docker-compose-linux-x86_64 && \
    cp /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY adk_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt ansible-core

# Copy wait script
COPY adk_agent/wait-for-ollama-ready.sh /app/wait-for-ollama-ready.sh
RUN chmod +x /app/wait-for-ollama-ready.sh

# Copy application files
COPY . .

EXPOSE 8100

# Use entrypoint to wait for Ollama before starting uvicorn
ENTRYPOINT ["/app/wait-for-ollama-ready.sh"]
CMD ["uvicorn", "adk_agent.main:app", "--host", "0.0.0.0", "--port", "8100"]