#!/bin/bash
echo "$(date)"
echo "Current date: $(date)"
echo "Press Enter to continue..."
read -r
wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/main/late/subtest.sh | bash
