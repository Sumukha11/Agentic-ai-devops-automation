terraform {
  required_version = ">= 1.5.0"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

resource "null_resource" "kind_cluster" {
  triggers = {
    cluster_name      = var.cluster_name
    kind_config       = filesha256("${path.module}/kind-cluster.yaml")
    loki_port_mapping = "31100:3100"
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      if kind get clusters | grep -Fxq "${var.cluster_name}"; then
        HOST_PORT_3100=$(docker port ${var.cluster_name}-control-plane 31100/tcp 2>/dev/null || true)
        HOST_PORT_3000=$(docker port ${var.cluster_name}-control-plane 30080/tcp 2>/dev/null || true)
        if ! printf '%s' "$HOST_PORT_3100" | grep -q '3100' || ! printf '%s' "$HOST_PORT_3000" | grep -q '3000'; then
          echo "Recreating stale Kind cluster ${var.cluster_name} because port mappings changed"
          kind delete cluster --name ${var.cluster_name}
          kind create cluster --name ${var.cluster_name} --config "${path.module}/kind-cluster.yaml" --wait 180s
        else
          echo "Kind cluster ${var.cluster_name} already exists with required port mappings"
        fi
      else
        kind create cluster --name ${var.cluster_name} --config "${path.module}/kind-cluster.yaml" --wait 180s
      fi
      docker network connect kind agent 2>/dev/null || true
      CONTROL_PLANE_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${var.cluster_name}-control-plane)
      kubectl config set-cluster kind-${var.cluster_name} --server="https://$CONTROL_PLANE_IP:7555"
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kind delete cluster --name ${self.triggers.cluster_name}"
  }
}

resource "null_resource" "grafana" {
  depends_on = [null_resource.kind_cluster, null_resource.kubeconfig, null_resource.loki]

  triggers = {
    cluster_name   = var.cluster_name
    manifest       = filesha256("${path.module}/grafana.yaml")
    dashboard_hash = filesha256("${path.module}/grafana-dashboard.yaml")
    cluster_id     = null_resource.kind_cluster.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      docker exec -i ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply --validate=false -f - < "${path.module}/grafana.yaml"
      docker exec -i ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply --validate=false -f - < "${path.module}/grafana-dashboard.yaml"
      docker exec ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring rollout status deployment/grafana --timeout=600s
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete deployment grafana --ignore-not-found >/dev/null 2>&1 || true; docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete service grafana --ignore-not-found >/dev/null 2>&1 || true; docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete secret grafana-admin --ignore-not-found >/dev/null 2>&1 || true; docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete configmap grafana-datasources grafana-dashboard-devops-resources grafana-dashboard-providers --ignore-not-found >/dev/null 2>&1 || true"
  }
}

resource "null_resource" "kubeconfig" {
  depends_on = [null_resource.kind_cluster]

  triggers = {
    cluster_name = var.cluster_name
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      mkdir -p "$HOME/.kube"
      kind get kubeconfig --name ${var.cluster_name} > "$HOME/.kube/config"
      docker network connect kind agent 2>/dev/null || true
      CONTROL_PLANE_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${var.cluster_name}-control-plane)
      kubectl config set-cluster kind-${var.cluster_name} --server="https://$CONTROL_PLANE_IP:7555"
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "rm -f $HOME/.kube/config"
  }
}

# Loki reconciliation resource
resource "null_resource" "loki" {
  depends_on = [null_resource.kind_cluster, null_resource.kubeconfig]

  triggers = {
    cluster_name = var.cluster_name
    manifest     = filesha256("${path.module}/loki.yaml")
    cluster_id   = null_resource.kind_cluster.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      docker exec -i ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply --validate=false -f - < "${path.module}/loki.yaml"
      docker exec ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring rollout status deployment/loki --timeout=180s
      docker exec ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring rollout status deployment/loki-gateway --timeout=180s
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete deployment loki loki-gateway --ignore-not-found >/dev/null 2>&1 || true; docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete service loki loki-gateway --ignore-not-found >/dev/null 2>&1 || true; docker exec ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring delete configmap loki-config loki-gateway-config --ignore-not-found >/dev/null 2>&1 || true"
  }
}
