resource "openstack_networking_network_v2" "tripleo_mgmt" {
  name           = "tripleo-mgmt-net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "tripleo_mgmt_subnet" {
  name       = "tripleo-mgmt-subnet"
  network_id = openstack_networking_network_v2.tripleo_mgmt.id
  cidr       = var.network_cidr
  ip_version = 4
  dns_nameservers = [var.dns_nameserver]

  allocation_pool {
    start = "10.10.0.10"
    end   = "10.10.0.200"
  }
}

resource "openstack_networking_router_v2" "tripleo_router" {
  name                = "tripleo-router"
  admin_state_up      = true
  external_network_id = data.openstack_networking_network_v2.external.id
}

resource "openstack_networking_router_interface_v2" "tripleo_router_interface" {
  router_id = openstack_networking_router_v2.tripleo_router.id
  subnet_id = openstack_networking_subnet_v2.tripleo_mgmt_subnet.id
}

resource "openstack_compute_keypair_v2" "tripleo_keypair" {
  name       = var.key_pair_name
  public_key = var.ssh_public_key
}

resource "openstack_networking_secgroup_v2" "tripleo_sg" {
  name        = "tripleo-sg"
  description = "Security group for undercloud and overcloud nodes"
}

resource "openstack_networking_secgroup_rule_v2" "icmp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "icmp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.tripleo_sg.id
}

resource "openstack_networking_secgroup_rule_v2" "ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.tripleo_sg.id
}

resource "openstack_networking_secgroup_rule_v2" "http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.tripleo_sg.id
}

resource "openstack_networking_secgroup_rule_v2" "https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.tripleo_sg.id
}

resource "openstack_compute_instance_v2" "undercloud" {
  name              = var.undercloud_name
  image_name        = var.image_name
  flavor_name       = var.undercloud_flavor
  key_pair          = openstack_compute_keypair_v2.tripleo_keypair.name
  security_groups   = [openstack_networking_secgroup_v2.tripleo_sg.name]

  user_data = <<-EOF
    #cloud-config
    hostname: ${var.undercloud_name}
    fqdn: ${var.undercloud_name}.example.local
    chpasswd:
      list: |
        root:${var.undercloud_root_password}
      expire: false
    packages:
      - git
      - python3
      - python3-pip
      - vim
      - curl
      - jq
    runcmd:
      - echo "export OS_CLOUD=default" >> /root/.bashrc
      - echo "export PATH=$PATH:/usr/local/bin" >> /root/.bashrc
      - echo "export OPENSTACK_RELEASE=16" >> /root/.bashrc
      - echo "Undercloud bootstrapped. Run the RHOS 16 TripleO undercloud install on this node." >> /root/.cloud-init.log
  EOF

  network {
    uuid = openstack_networking_network_v2.tripleo_mgmt.id
  }
}

resource "openstack_compute_instance_v2" "controller" {
  name            = var.controller_name
  image_name      = var.image_name
  flavor_name     = var.controller_flavor
  key_pair        = openstack_compute_keypair_v2.tripleo_keypair.name
  security_groups = [openstack_networking_secgroup_v2.tripleo_sg.name]

  network {
    uuid = openstack_networking_network_v2.tripleo_mgmt.id
  }
}

resource "openstack_compute_instance_v2" "compute" {
  name            = var.compute_name
  image_name      = var.image_name
  flavor_name     = var.compute_flavor
  key_pair        = openstack_compute_keypair_v2.tripleo_keypair.name
  security_groups = [openstack_networking_secgroup_v2.tripleo_sg.name]

  network {
    uuid = openstack_networking_network_v2.tripleo_mgmt.id
  }
}

data "openstack_networking_network_v2" "external" {
  name = var.external_network
}
