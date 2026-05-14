output "undercloud_ip" {
  description = "External IP of the undercloud VM"
  value       = libvirt_domain.undercloud.network_interface[0].addresses
}

output "controller_mac_addresses" {
  description = "Provisioning NIC MACs for controllers (needed for Ironic)"
  value = {
    for i, ctrl in libvirt_domain.controller :
    ctrl.name => ctrl.network_interface[0].mac
  }
}

output "compute_mac_addresses" {
  description = "Provisioning NIC MACs for compute nodes"
  value = {
    for i, comp in libvirt_domain.compute :
    comp.name => comp.network_interface[0].mac
  }
}

output "ceph_mac_addresses" {
  description = "Provisioning NIC MACs for Ceph nodes"
  value = {
    for i, ceph in libvirt_domain.ceph :
    ceph.name => ceph.network_interface[0].mac
  }
}

output "network_summary" {
  value = {
    provisioning  = var.provisioning_network_cidr
    external      = var.external_network_cidr
    internal_api  = var.internal_api_network_cidr
    tenant        = var.tenant_network_cidr
    storage       = var.storage_network_cidr
    storage_mgmt  = var.storage_mgmt_network_cidr
  }
}
