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
    cluster_name = var.cluster_name
    kind_config  = filesha256("${path.module}/kind-cluster.yaml")
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      if kind get clusters | grep -Fxq "${var.cluster_name}"; then
        echo "Kind cluster ${var.cluster_name} already exists"
      else
        kind create cluster --name ${var.cluster_name} --config "${path.module}/kind-cluster.yaml" --wait 180s
        docker network connect kind agent 2>/dev/null || true
        CONTROL_PLANE_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${var.cluster_name}-control-plane)
        kubectl config set-cluster kind-${var.cluster_name} --server="https://$CONTROL_PLANE_IP:7555"
      fi
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kind delete cluster --name ${self.triggers.cluster_name}"
  }
}

resource "null_resource" "grafana" {
  depends_on = [null_resource.kind_cluster, null_resource.kubeconfig]

  triggers = {
    cluster_name = var.cluster_name
    manifest     = filesha256("${path.module}/grafana.yaml")
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      docker exec -i ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply --validate=false -f - < "${path.module}/grafana.yaml"
      docker exec ${var.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf -n monitoring rollout status deployment/grafana --timeout=180s
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "docker exec -i ${self.triggers.cluster_name}-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf delete -f - --ignore-not-found < grafana.yaml 2>/dev/null || true"
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
