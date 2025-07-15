#!/bin/bash
# Instructions:
# lead all commands with
# echo " " && echo " " && echo " "
# to easily spot the commands and the responses in Subiquity late run command.
echo "---------------------------------------------------------"
echo " " && echo " " && echo "This is a test run of sub script."

echo " " && echo " " && echo "dpkg -l | grep iputils-ping"
dpkg -l | grep iputils-ping

echo " " && echo " " && echo "apt install iputils-ping -y"
apt install iputils-ping -y

echo " " && echo " " && echo "dpkg -l | grep iputils-ping"
dpkg -l | grep iputils-ping

echo " " && echo " "
