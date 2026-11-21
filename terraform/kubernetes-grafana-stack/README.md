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
