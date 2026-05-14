# ──────────────────────────────────────────────
# Provisioning / Control Plane Network
# ──────────────────────────────────────────────
resource "libvirt_network" "provisioning" {
  name      = "tripleo-provisioning"
  mode      = "nat"
  domain    = "provisioning.local"
  autostart = true

  addresses = [var.provisioning_network_cidr]

  dhcp { enabled = false }

  dns { enabled = true }
}

# ──────────────────────────────────────────────
# External Network
# ──────────────────────────────────────────────
resource "libvirt_network" "external" {
  name      = "tripleo-external"
  mode      = "nat"
  domain    = "external.local"
  autostart = true

  addresses = [var.external_network_cidr]

  dhcp { enabled = true }

  dns { enabled = true }
}

# ──────────────────────────────────────────────
# Internal API Network
# ──────────────────────────────────────────────
resource "libvirt_network" "internal_api" {
  name      = "tripleo-internal-api"
  mode      = "none"
  autostart = true

  addresses = [var.internal_api_network_cidr]

  dhcp { enabled = false }
}

# ──────────────────────────────────────────────
# Tenant Network
# ──────────────────────────────────────────────
resource "libvirt_network" "tenant" {
  name      = "tripleo-tenant"
  mode      = "none"
  autostart = true

  addresses = [var.tenant_network_cidr]

  dhcp { enabled = false }
}

# ──────────────────────────────────────────────
# Storage Network
# ──────────────────────────────────────────────
resource "libvirt_network" "storage" {
  name      = "tripleo-storage"
  mode      = "none"
  autostart = true

  addresses = [var.storage_network_cidr]

  dhcp { enabled = false }
}

# ──────────────────────────────────────────────
# Storage Management Network
# ──────────────────────────────────────────────
resource "libvirt_network" "storage_mgmt" {
  name      = "tripleo-storage-mgmt"
  mode      = "none"
  autostart = true

  addresses = [var.storage_mgmt_network_cidr]

  dhcp { enabled = false }
}
