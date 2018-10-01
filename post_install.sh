#!/bin/bash

# For cfncluster post-install step

# EFS
mkdir -p /efs
echo "fs-xxxxxx.efs.us-east-1.amazonaws.com:/ /efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0" >> /etc/fstab
mount -a -t nfs4

# Additional packages
/shared/apps/cluster_setup/install_packages.sh

# Timezone
sed -i '/ZONE/s/UTC/America\/Chicago/' /etc/sysconfig/clock
ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime
reboot
