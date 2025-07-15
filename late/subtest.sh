#!/bin/bash
echo; echo
echo -e "\033[32mThis is a test run of sub script.\033[0m"

echo; echo
echo "$(date)"
echo "Current date: $(date)"

echo; echo
dpkg -l | grep iputils-ping
echo; echo
# apt install iputils-ping -y
echo; echo
dpkg -l | grep iputils-ping
echo; echo
