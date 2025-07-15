#!/bin/bash
echo; echo
echo -e "\033[32mThis is a test run of sub script.\033[0m"

echo; echo
echo "$(date)"
echo "Current date: $(date)"

echo " " && echo " "
curtin in-target -- dpkg -l | grep iputils-ping
echo; echo
curtin in-target -- apt install iputils-ping -y
echo; echo
curtin in-target -- dpkg -l | grep iputils-ping
echo; echo
