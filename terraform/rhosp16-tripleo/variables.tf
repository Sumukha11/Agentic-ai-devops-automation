variable "region" {
  description = "OpenStack region for the deployment"
  type        = string
  default     = "RegionOne"
}

variable "external_network" {
  description = "Existing external network name used for floating IPs"
  type        = string
  default     = "public"
}

variable "image_name" {
  description = "Image name to use for Undercloud and Overcloud nodes"
  type        = string
  default     = "rhel-9.4-x86_64"
}

variable "undercloud_flavor" {
  description = "Flavor for the Undercloud VM"
  type        = string
  default     = "m1.xlarge"
}

variable "controller_flavor" {
  description = "Flavor for the Controller node"
  type        = string
  default     = "m1.xlarge"
}

variable "compute_flavor" {
  description = "Flavor for the Compute node"
  type        = string
  default     = "m1.large"
}

variable "key_pair_name" {
  description = "SSH key pair name already available in OpenStack"
  type        = string
  default     = "tripleo-key"
}

variable "ssh_public_key" {
  description = "Public SSH key used for the provisioned nodes"
  type        = string
  default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1example"
}

variable "undercloud_name" {
  description = "Name for the Undercloud node"
  type        = string
  default     = "rhosp16-undercloud"
}

variable "controller_name" {
  description = "Name for the Controller node"
  type        = string
  default     = "rhosp16-controller-0"
}

variable "compute_name" {
  description = "Name for the Compute node"
  type        = string
  default     = "rhosp16-compute-0"
}

variable "network_cidr" {
  description = "Private network CIDR for the TripleO environment"
  type        = string
  default     = "10.10.0.0/24"
}

variable "dns_nameserver" {
  description = "DNS server for the private network"
  type        = string
  default     = "8.8.8.8"
}

variable "undercloud_root_password" {
  description = "Root password used on the undercloud instance for local admin tasks"
  type        = string
  default     = "ChangeMe123!"
  sensitive   = true
}

variable "stack_name" {
  description = "Overcloud stack name used by TripleO"
  type        = string
  default     = "overcloud"
}
