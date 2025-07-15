#!/bin/bash
# Instructions:
# lead all commands with
# echo " " && echo " " && echo " "
# to easily spot the commands and the responses in Subuquity late run command.
echo "--------------------------------------------------------------------------
echo " " && echo " " && echo "This is a test run of Subiquity late run command."
echo " " && echo " " && echo "$(date)"

echo " " && echo " " && echo "curtin in-target -- apt update -y"
curtin in-target -- apt update -y

echo " " && echo " " && echo "curtin in-target -- apt install wget -y"
curtin in-target -- apt install wget -y

echo " " && echo " " && echo "curtin in-target -- dpkg -l | grep openssh-server"
curtin in-target -- dpkg -l | grep openssh-server

echo " " && echo " " && echo "curtin in-target -- apt install openssh-server -y"
curtin in-target -- apt install openssh-server -y

echo " " && echo " " && echo "curtin in-target -- dpkg -l | grep openssh-server"
curtin in-target -- dpkg -l | grep openssh-server

wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/subtest.sh | bash
