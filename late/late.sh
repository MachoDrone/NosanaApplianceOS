#!/bin/bash
# Instructions:
# lead all commands with
# echo; echo; echo ""
# to spot the command and response in Subuquity late run command.

printf "\n\n \n"
printf "\n\ntestmessage\n"
echo "This is a test run of Subiquity late run command."

echo " " && echo " "
echo; echo; echo "sleep 3"
sleep 3

echo; echo; echo "$(date)"
echo "Current date: $(date)"

echo " " && echo "curtin in-target -- apt update -y"
curtin in-target -- apt update -y
echo " " && echo "curtin in-target -- apt install wget -y"
curtin in-target -- apt install wget -y

echo; echo; echo "dpkg -l | grep openssh-server"
 dpkg -l | grep openssh-server

echo; echo; echo "apt install openssh-server -y"
curtin in-target -- apt install openssh-server -y

echo; echo; echo "dpkg -l | grep openssh-server"
dpkg -l | grep openssh-server


echo " " && echo " " && echo "-----------Actual subtest.sh--------------"
for i in {1..3}; do
  if curtin in-target -- bash -c "wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/late.sh | bash"; then
    echo "Success!"
    break
  else
    echo "Attempt $i failed, retrying in 10 seconds..."
    sleep 10
  fi
done

echo " " && echo " " && echo "-----------fake out fails--------------"
for i in {1..3}; do
  if curtin in-target -- bash -c "wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/subtest2.bat | bash"; then
    echo "Success!"
    break
  else
    echo "Attempt $i failed, retrying in 10 seconds..."
    sleep 10
  fi
done

#wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/subtest.sh | bash

# The follwing did not print, pause, nor did they show an error.
#echo "$(date)"
#echo "Current date: $(date)"
#echo "Press Enter to continue..."
#read -r
