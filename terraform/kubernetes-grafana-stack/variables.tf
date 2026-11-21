variable "cluster_name" {
  description = "Name of the local Kind Kubernetes cluster"
  type        = string
  default     = "devops-grafana"
}

variable "grafana_admin_user" {
  description = "Grafana administrator username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "grafana_admin_password" {
  description = "Grafana administrator password"
  type        = string
  default     = "admin"
  sensitive   = true
}
