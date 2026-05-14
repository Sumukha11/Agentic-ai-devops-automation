# ════════════════════════════════════════════════
#  CEPH / STORAGE NODES
# ════════════════════════════════════════════════
resource "libvirt_volume" "ceph_os_disk" {
  count          = var.ceph_count
  name           = "ceph-${count.index}-os.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.base_image.id
  size           = var.ceph_os_disk_gb * 1073741824
  format         = "qcow2"
}

# Separate OSD disks (raw, no base image)
resource "libvirt_volume" "ceph_osd_disk_a" {
  count  = var.ceph_count
  name   = "ceph-${count.index}-osd-a.qcow2"
  pool   = "default"
  size   = var.ceph_osd_disk_gb * 1073741824
  format = "qcow2"
}

resource "libvirt_volume" "ceph_osd_disk_b" {
  count  = var.ceph_count
  name   = "ceph-${count.index}-osd-b.qcow2"
  pool   = "default"
  size   = var.ceph_osd_disk_gb * 1073741824
  format = "qcow2"
}

resource "libvirt_domain" "ceph" {
  count  = var.ceph_count
  name   = "tripleo-ceph-${count.index}"
  memory = var.ceph_memory_mb
  vcpu   = var.ceph_vcpus

  cpu {
    mode = "host-passthrough"
  }

  boot_device {
    dev = ["network", "hd"]
  }

  # OS disk
  disk {
    volume_id = libvirt_volume.ceph_os_disk[count.index].id
    scsi      = false
  }

  # OSD disk A
  disk {
    volume_id = libvirt_volume.ceph_osd_disk_a[count.index].id
    scsi      = false
  }

  # OSD disk B
  disk {
    volume_id = libvirt_volume.ceph_osd_disk_b[count.index].id
    scsi      = false
  }

  # Provisioning
  network_interface {
    network_id     = libvirt_network.provisioning.id
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
