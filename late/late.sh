#!/bin/bash
# apt-get update -y
dpkg -l | grep openssh
apt install openssh-server -y
dpkg -l | grep openssh-server
dpkg -l | grep openssh

wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/subtest.sh | bash

# The follwing did not print, pause, nor did they show an error.
#echo "$(date)"
#echo "Current date: $(date)"
#echo "Press Enter to continue..."
#read -r
