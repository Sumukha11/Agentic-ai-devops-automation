# ════════════════════════════════════════════════
#  CONTROLLERS
# ════════════════════════════════════════════════
resource "libvirt_volume" "controller_disk" {
  count          = var.controller_count
  name           = "controller-${count.index}-os.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.base_image.id
  size           = var.controller_disk_gb * 1073741824
  format         = "qcow2"
}

resource "libvirt_domain" "controller" {
  count  = var.controller_count
  name   = "tripleo-controller-${count.index}"
  memory = var.controller_memory_mb
  vcpu   = var.controller_vcpus

  cpu {
    mode = "host-passthrough"
  }

  # PXE boot from provisioning network
  boot_device {
    dev = ["network", "hd"]
  }

  disk {
    volume_id = libvirt_volume.controller_disk[count.index].id
    scsi      = false
  }

  # Provisioning / PXE
  network_interface {
    network_id     = libvirt_network.provisioning.id
    wait_for_lease = false
  }

  # Internal API
  network_interface {
    network_id     = libvirt_network.internal_api.id
    wait_for_lease = false
  }

  # Tenant
  network_interface {
    network_id     = libvirt_network.tenant.id
    wait_for_lease = false
  }

  # Storage
  network_interface {
    network_id     = libvirt_network.storage.id
    wait_for_lease = false
  }

  # Storage Management
  network_interface {
    network_id     = libvirt_network.storage_mgmt.id
    wait_for_lease = false
  }

  # External
  network_interface {
    network_id     = libvirt_network.external.id
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

# ════════════════════════════════════════════════
#  COMPUTE NODES
# ════════════════════════════════════════════════
resource "libvirt_volume" "compute_disk" {
  count          = var.compute_count
  name           = "compute-${count.index}-os.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.base_image.id
  size           = var.compute_disk_gb * 1073741824
  format         = "qcow2"
}

resource "libvirt_domain" "compute" {
  count  = var.compute_count
  name   = "tripleo-compute-${count.index}"
  memory = var.compute_memory_mb
  vcpu   = var.compute_vcpus

  cpu {
    mode = "host-passthrough"
  }

  boot_device {
    dev = ["network", "hd"]
  }

  disk {
    volume_id = libvirt_volume.compute_disk[count.index].id
    scsi      = false
  }

  # Provisioning
  network_interface {
    network_id     = libvirt_network.provisioning.id
    wait_for_lease = false
  }

  # Internal API
  network_interface {
    network_id     = libvirt_network.internal_api.id
    wait_for_lease = false
  }

  # Tenant
  network_interface {
    network_id     = libvirt_network.tenant.id
    wait_for_lease = false
  }

  # Storage
  network_interface {
    network_id     = libvirt_network.storage.id
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
