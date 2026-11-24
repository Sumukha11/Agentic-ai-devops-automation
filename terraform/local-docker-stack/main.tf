terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

data "docker_network" "devops_network" {
  name = var.docker_network_name
}

resource "docker_container" "prometheus_server" {
  name  = "prometheus-server"
  image = "prom/prometheus:latest"

  ports {
    internal = 9090
    external = 9090
  }

  mounts {
    target    = "/etc/prometheus/prometheus.yml"
    source    = var.prometheus_config_path
    type      = "bind"
    read_only = true
  }

  networks_advanced {
    name = data.docker_network.devops_network.name
  }

  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--web.enable-lifecycle"
  ]
}

