variable "docker_network_name" {
  description = "Docker network for the Prometheus deployment"
  type        = string
  default     = "prometheus-net"
}

variable "jenkins_port" {
  description = "Port exposed for Jenkins"
  type        = number
  default     = 8080
}

variable "fastapi_port" {
  description = "Port exposed for FastAPI"
  type        = number
  default     = 8000
}

variable "streamlit_port" {
  description = "Port exposed for Streamlit"
  type        = number
  default     = 8501
}

variable "ollama_port" {
  description = "Port exposed for Ollama"
  type        = number
  default     = 11434
}

variable "prometheus_config_path" {
  description = "Absolute host path to the Prometheus config file used by the Docker bind mount"
  type        = string
  default     = "/home/sumukha/Desktop/IITP-Project/Agentic-ai-devops-automation/terraform/local-docker-stack/prometheus/prometheus.yml"
}
