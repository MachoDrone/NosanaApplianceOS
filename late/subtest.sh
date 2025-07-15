#!/bin/bash
echo "$(date)"
echo "Current date: $(date)"

dpkg -l | grep iputils-ping
apt install iputils-ping -y
dpkg -l | grep iputils-ping
