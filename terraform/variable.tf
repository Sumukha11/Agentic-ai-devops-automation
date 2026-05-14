# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────
variable "libvirt_uri" {
  description = "Libvirt connection URI"
  type        = string
  default     = "qemu:///system"
}

variable "base_image_url" {
  description = "URL or local path to the CentOS/RHEL 9 cloud image"
  type        = string
  default     = "[cloud.centos.org](https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2)"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

# ──────────────────────────────────────────────
# Undercloud
# ──────────────────────────────────────────────
variable "undercloud_vcpus" {
  type    = number
  default = 4
}

variable "undercloud_memory_mb" {
  type    = number
  default = 16384 # 16 GB
}

variable "undercloud_disk_gb" {
  type    = number
  default = 100
}

# ──────────────────────────────────────────────
# Overcloud Controllers
# ──────────────────────────────────────────────
variable "controller_count" {
  type    = number
  default = 3
}

variable "controller_vcpus" {
  type    = number
  default = 4
}

variable "controller_memory_mb" {
  type    = number
  default = 16384
}

variable "controller_disk_gb" {
  type    = number
  default = 80
}

# ──────────────────────────────────────────────
# Overcloud Compute Nodes
# ──────────────────────────────────────────────
variable "compute_count" {
  type    = number
  default = 2
}

variable "compute_vcpus" {
  type    = number
  default = 4
}

variable "compute_memory_mb" {
  type    = number
  default = 8192
}

variable "compute_disk_gb" {
  type    = number
  default = 80
}

# ──────────────────────────────────────────────
# Overcloud Ceph / Storage Nodes
# ──────────────────────────────────────────────
variable "ceph_count" {
  type    = number
  default = 3
}

variable "ceph_vcpus" {
  type    = number
  default = 2
}

variable "ceph_memory_mb" {
  type    = number
  default = 8192
}

variable "ceph_osd_disk_gb" {
  type    = number
  default = 50
}

variable "ceph_os_disk_gb" {
  type    = number
  default = 50
}

# ──────────────────────────────────────────────
# Networking
# ──────────────────────────────────────────────
variable "provisioning_network_cidr" {
  type    = string
  default = "192.168.24.0/24"
}

variable "external_network_cidr" {
  type    = string
  default = "10.0.0.0/24"
}

variable "tenant_network_cidr" {
  type    = string
  default = "172.16.0.0/24"
}

variable "storage_network_cidr" {
  type    = string
  default = "172.18.0.0/24"
}

variable "storage_mgmt_network_cidr" {
  type    = string
  default = "172.19.0.0/24"
}

variable "internal_api_network_cidr" {
  type    = string
  default = "172.17.0.0/24"
}
