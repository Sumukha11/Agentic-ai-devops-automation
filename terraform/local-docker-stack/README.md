# Free Terraform DevOps Stack

This Terraform project is a practical alternative to a paid OpenStack/Terraform setup.
It provisions a local Docker-based DevOps environment using the Docker provider, which works without Keystone credentials or cloud subscriptions.

## What it creates

- Jenkins on port 8080
- FastAPI service on port 8000
- Streamlit UI on port 8501
- Ollama service on port 11434
- Shared Docker network: `devops-net`

## Usage

```bash
cd terraform/local-docker-stack
terraform init
terraform plan
terraform apply -auto-approve
```

## Why this is better here

This repo already contains Docker Compose services for Jenkins, FastAPI, Streamlit, and Ollama.
This Terraform project matches that use case but keeps everything local and free.

## Cleanup

```bash
terraform destroy -auto-approve
```
