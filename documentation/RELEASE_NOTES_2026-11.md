# Release Notes — 21 November 2026

## Version 4.0

### Kubernetes and Grafana
- Added a local Kind Kubernetes Terraform project at `terraform/kubernetes-grafana-stack`.
- Added Grafana deployment in the `monitoring` namespace.
- Grafana is available on `http://localhost:3000` with `admin` / `admin` credentials.
- The agent can deploy and destroy this stack through natural-language Terraform actions.

### Jenkins Job Reconciliation
- Removed legacy Jenkins duplicate jobs.
- Added canonical reconciliation for:
  - `API-Health-Check`
  - `Git-Repository-Clone`
  - `Yahoo-Stock-Scraper`
- Existing canonical jobs are updated from repository Groovy scripts on initialization.
- Added descriptions to canonical Jenkins pipeline jobs.

### Jenkins Trigger Reliability
- Jenkins build triggering now returns immediately with `QUEUED` and no artificial build-number assumption.
- Agent and FastAPI request timeouts were separated from actual build runtime.
- Status requests support individual jobs and all Jenkins jobs.
- Batch triggering supports `trigger_builds` for multiple jobs.

### Ollama and LLM Performance
- Replaced `llama3` as the agent's default model with `qwen2.5:3b`.
- Qwen 2.5 3B is smaller and faster for strict JSON tool-routing in this project.
- The agent uses deterministic generation options and limited context/output size.
- Ollama keeps the model resident for 24 hours.
- Startup waits for Ollama and the configured model before starting the agent API.
- The startup warmup loads Qwen before normal user interaction.

### Docker and Kind
- The agent image includes Terraform, Kind, kubectl, and Docker CLI access.
- The agent mounts `/var/run/docker.sock` and the host Docker CLI.
- Grafana manifests are applied inside the Kind control-plane container for reliable local deployment.

### Grafana UI Rendering
- Streamlit recognizes Kubernetes/Grafana deployment responses.
- Grafana URL and default credentials are displayed after successful deployment.
