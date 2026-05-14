terraform {
  required_version = ">= 1.5"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.7"
    }
  }
}

provider "libvirt" {
  uri = var.libvirt_uri
}

# ──────────────────────────────────────────────
# Base Image Volume (backing store for all VMs)
# ──────────────────────────────────────────────
resource "libvirt_volume" "base_image" {
  name   = "tripleo-base-image.qcow2"
  pool   = "default"
  source = var.base_image_url
  format = "qcow2"
}

# ──────────────────────────────────────────────
# Cloud-init for Undercloud
# ──────────────────────────────────────────────
data "template_file" "undercloud_user_data" {
  template = <<-EOF
    #cloud-config
    hostname: undercloud
    fqdn: undercloud.localdomain
    manage_etc_hosts: true
    users:
      - name: stack
        sudo: ALL=(ALL) NOPASSWD:ALL
        groups: wheel
        shell: /bin/bash
        ssh_authorized_keys:
          - ${var.ssh_public_key}
    packages:
      - python3
      - vim
      - git
      - tmux
    runcmd:
      - echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
      - sysctl -p
      - useradd -m stack || true
      - echo "stack ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/stack
    write_files:
      - path: /home/stack/undercloud.conf
        owner: stack:stack
        permissions: '0644'
        content: |
          [DEFAULT]
          undercloud_hostname = undercloud.localdomain
          local_ip = 192.168.24.1/24
          undercloud_public_host = 192.168.24.2
          undercloud_admin_host = 192.168.24.3
          local_interface = eth1
          masquerade_network = 192.168.24.0/24
          generate_service_certificate = false
          undercloud_ntp_servers = pool.ntp.org

          [ctlplane-subnet]
          cidr = 192.168.24.0/24
          dhcp_start = 192.168.24.5
          dhcp_end = 192.168.24.55
          inspection_iprange = 192.168.24.100,192.168.24.120
          gateway = 192.168.24.1
  EOF
}

resource "libvirt_cloudinit_disk" "undercloud_init" {
  name      = "undercloud-cloudinit.iso"
  pool      = "default"
  user_data = data.template_file.undercloud_user_data.rendered
}
