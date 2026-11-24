output "cluster_name" {
  description = "Kind cluster name"
  value       = var.cluster_name
}

output "grafana_url" {
  description = "Grafana URL on the local host"
  value       = "http://localhost:3000"
}

output "grafana_credentials" {
  description = "Default Grafana credentials"
  value = {
    username = var.grafana_admin_user
    password = var.grafana_admin_password
  }
  sensitive = true
}

output "loki_url" {
  description = "Loki HTTP API URL on the local host"
  value       = "http://localhost:3100"
}
