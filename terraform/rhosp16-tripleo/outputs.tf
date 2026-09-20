output "undercloud_private_ip" {
  description = "Private IP of the undercloud instance"
  value       = openstack_compute_instance_v2.undercloud.access_ip_v4
}

output "controller_private_ip" {
  description = "Private IP of the controller instance"
  value       = openstack_compute_instance_v2.controller.access_ip_v4
}

output "compute_private_ip" {
  description = "Private IP of the compute instance"
  value       = openstack_compute_instance_v2.compute.access_ip_v4
}

output "network_id" {
  description = "TripleO management network ID"
  value       = openstack_networking_network_v2.tripleo_mgmt.id
}

output "security_group_id" {
  description = "Security group for TripleO nodes"
  value       = openstack_networking_secgroup_v2.tripleo_sg.id
}

output "next_steps" {
  description = "Commands to run inside the undercloud after deployment"
  value = <<EOT
  ssh root@${openstack_compute_instance_v2.undercloud.access_ip_v4}
  sudo subscription-manager register --username <USERNAME> --password <PASSWORD> --auto-attach
  sudo subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
  sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
  sudo dnf install -y python3-tripleoclient
  sudo openstack undercloud install
  source ~/stackrc
  openstack server list
  openstack image list
  openstack network list
  openstack overcloud deploy --templates
EOT
}
