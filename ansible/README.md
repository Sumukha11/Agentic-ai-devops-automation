# Ansible Observability Playbooks

## Prerequisites

- Docker and Docker Compose
- Ansible
- Kind and kubectl for Grafana/Loki

## Playbooks

1. Deploy Prometheus and all metric exporters:

```bash
ansible-playbook -i ansible/inventory.ini ansible/prometheus.yml
```

2. Provision the Grafana Prometheus/Loki datasources and resource dashboard:

```bash
ansible-playbook -i ansible/inventory.ini ansible/grafana-dashboard.yml
```

3. Deploy Loki and collect Docker container logs:

```bash
ansible-playbook -i ansible/inventory.ini ansible/loki-logs.yml
```

## Endpoints

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Dashboard: http://localhost:3000/d/devops-resources/devops-resource-monitoring
- Loki: http://localhost:3100
- Ollama exporter: http://localhost:9108/metrics
- cAdvisor: http://localhost:8081
- Node exporter: http://localhost:9100
