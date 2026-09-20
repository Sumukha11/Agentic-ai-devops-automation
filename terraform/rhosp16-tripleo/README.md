# RHOS 16 TripleO Terraform Deployment Scaffold

This directory contains a Terraform deployment scaffold for a minimal Red Hat OpenStack Platform 16 (RHOS 16) TripleO environment.

## Architecture

- Undercloud VM: hosts the TripleO undercloud and runs `openstack` commands
- Controller node: primary overcloud controller
- Compute node: overcloud compute
- Shared management network and security group

This project is intended to provision the underlying VM/network infrastructure that supports RHOS 16 TripleO, and then the actual OpenStack stack is installed and deployed from the undercloud using the standard TripleO workflow.

## Prerequisites

1. A working OpenStack cloud with credentials exported as environment variables
2. Terraform installed locally
3. A valid image name in the target OpenStack project
4. A public external network available for floating IPs
5. A keypair already created in OpenStack

Example environment:

```bash
export OS_AUTH_URL=https://<keystone-endpoint>:5000/v3
export OS_USERNAME=<username>
export OS_PASSWORD=<password>
export OS_PROJECT_NAME=<project>
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME=RegionOne
```

## Usage

```bash
cd terraform/rhosp16-tripleo
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply -auto-approve
```

## Important: full RHOS 16 deployment

Terraform will create the undercloud and overcloud infrastructure nodes, but the actual cloud deployment still requires the standard TripleO undercloud flow:

```bash
ssh root@<UNDERCLOUD_PRIVATE_IP>
subscription-manager register --username <USERNAME> --password <PASSWORD> --auto-attach
subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
dnf install -y python3-tripleoclient
openstack undercloud install
source ~/stackrc
openstack server list
openstack image list
openstack network list
openstack overcloud deploy --templates
```

## Basic OpenStack commands that should work once the undercloud is ready

```bash
openstack server list
openstack image list
openstack network list
openstack subnet list
openstack flavor list
openstack project list
openstack user list
openstack stack list
```

## Notes

- This is a deployment scaffold for RHOS 16 / TripleO.
- For a production RHOS 16 environment, use the official Red Hat deployment guidance and validated image/host sizing.
- The actual undercloud installation and overcloud deployment remain a Red Hat administrator task after Terraform has provisioned the hosts.
