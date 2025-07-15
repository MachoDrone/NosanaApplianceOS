#!/bin/bash
# Instructions:
# lead all commands with
# echo " " && echo " " && echo " "
# to easily spot the commands and the responses in Subuquity late run command.
echo " " && echo " " && echo "curtin in-target -- dpkg -l | grep openssh-server"
curtin in-target -- dpkg -l | grep openssh-server

echo -----------------------------------------------------------
echo " " && echo " " && echo "This is a test run of sub script."

echo " " && echo " " && echo "curtin in-target -- dpkg -l | grep iputils-ping"
curtin in-target -- dpkg -l | grep iputils-ping

echo " " && echo " " && echo "curtin in-target -- apt install iputils-ping -y"
curtin in-target -- apt install iputils-ping -y

echo " " && echo " " && echo "curtin in-target -- dpkg -l | grep iputils-ping"
curtin in-target -- dpkg -l | grep iputils-ping

echo " " && echo " " 
