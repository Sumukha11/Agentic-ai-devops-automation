# Local Kubernetes Cluster with Grafana

This Terraform project creates a local Kind (Kubernetes in Docker) cluster named `devops-grafana` and deploys Grafana into the `monitoring` namespace.

## Deploy

```bash
cd terraform/kubernetes-grafana-stack
terraform init
terraform apply -auto-approve
```

Open http://localhost:3000

Default credentials:

- Username: `admin`
- Password: `admin`

## Verify Kubernetes

```bash
kubectl get nodes --context kind-devops-grafana
kubectl get pods -n monitoring --context kind-devops-grafana
kubectl get service -n monitoring --context kind-devops-grafana
```

## Destroy

```bash
terraform destroy -auto-approve
```

The project can also be deployed or destroyed through the AI agent with prompts such as:

- `Deploy a Kubernetes cluster with Grafana`
- `Destroy the Kubernetes Grafana deployment`

## Loki

Loki is deployed into the `monitoring` namespace when this stack is applied. Grafana is provisioned with Loki as a default datasource.

- Grafana: http://localhost:3000
- Loki browser status page: http://localhost:3100
- Loki readiness endpoint: http://localhost:3100/ready
- Loki HTTP API: http://localhost:3100/loki/api/v1/
- Grafana service credentials: `admin` / `admin`

Send logs to Loki using its native push endpoint:

```bash
curl -H 'Content-Type: application/json' -XPOST 'http://localhost:3100/loki/api/v1/push' --data-raw '{"streams":[{"stream":{"job":"demo"},"values":[["'$(date +%s)'000000000","hello from loki"]]}]}'
```

The AI agent can deploy or destroy it with:

- `Deploy Loki in Kubernetes`
- `Destroy the Loki Kubernetes deployment`
