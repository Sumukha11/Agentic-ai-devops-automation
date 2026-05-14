# ──────────────────────────────────────────────
# Undercloud OS Disk
# ──────────────────────────────────────────────
resource "libvirt_volume" "undercloud_disk" {
  name           = "undercloud-os.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.base_image.id
  size           = var.undercloud_disk_gb * 1073741824 # bytes
  format         = "qcow2"
}

# ──────────────────────────────────────────────
# Undercloud VM
# ──────────────────────────────────────────────
resource "libvirt_domain" "undercloud" {
  name   = "tripleo-undercloud"
  memory = var.undercloud_memory_mb
  vcpu   = var.undercloud_vcpus

  cloudinit = libvirt_cloudinit_disk.undercloud_init.id

  cpu {
    mode = "host-passthrough"
  }

  disk {
    volume_id = libvirt_volume.undercloud_disk.id
    scsi      = false
  }

  # NIC 1 — External / management
  network_interface {
    network_id     = libvirt_network.external.id
    wait_for_lease = true
  }

  # NIC 2 — Provisioning (control plane)
  network_interface {
    network_id     = libvirt_network.provisioning.id
    wait_for_lease = false
  }

  console {
    type        = "pty"
    target_type = "serial"
    target_port = "0"
  }

  graphics {
    type        = "vnc"
    listen_type = "address"
    autoport    = true
  }
}
