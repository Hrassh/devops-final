#!/bin/bash
set -e
dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user
