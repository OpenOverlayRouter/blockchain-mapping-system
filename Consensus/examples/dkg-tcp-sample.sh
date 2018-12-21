#!/bin/bash
set -euo pipefail

function LogAndExit_
{
    printf "\033[0;91m$1\n"
    printf "Terminating...\033[0m\n"
    exit 1
}

function ValidText_
{
    printf "\033[92m$1\033[0m\n"
}

trap "kill 0" EXIT

topDir=$(git rev-parse --show-toplevel)
utilsDir="$topDir/Consensus/examples/tcp-utils"
port=1111
amountMembers=0
aux=""
if [ -f "$utilsDir"/members.txt ]; then
    members=($(cat "$utilsDir"/members.txt))
    amountMembers=${#members[@]}
    threshold=$((amountMembers/2 + 1))
fi

# MEMBERS
echo "-------------------------------------"
if [ $amountMembers -gt 0 ]; then
    echo "Members ($amountMembers) are:"
    echo "${members[*]}"
    read -p "Do you want to generate a new list of members? (y/N) " aux
fi

if [ $amountMembers -eq 0 -o "$aux" == "y" ]; then
    read -p "Indicate lowest id that can be generated (default is 10000) " low
    if ! [[ $low =~ ^[-+]?[0-9]+$ ]]; then
        low=10000
    fi

    read -p "Indicate highest id that can be generated (default is 30000) " high
    if ! [[ $high =~ ^[-+]?[0-9]+$ ]]; then
        high=30000
    fi

    read -p "Indicate amount of ids that will be generated (default is 100) " amount
    if ! [[ $amount =~ ^[-+]?[0-9]+$ ]]; then
        amount=100
    fi
    "$utilsDir"/genMembers.sh "$low" "$high" "$amount"
    members=($(cat "$utilsDir"/members.txt))
    amountMembers=${#members[@]}
    threshold=$((amountMembers/2 + 1))
fi

ValidText_ "\nThere are $amountMembers members"
# THRESHOLD
echo "-------------------------------------"
read -p "Indicate a new threshold or press enter for default($threshold) " aux
if [ -n "$aux" ]; then
    threshold=$aux
fi

echo -e "Validating threshold $threshold...\n"
if ! [[ $threshold =~ ^[-+]?[0-9]+$ ]]; then
    LogAndExit_ "Invalid threshold, must be an integer!"
fi

if [ $threshold -gt $amountMembers -o $threshold -lt 2 ]; then
    LogAndExit_ "Invalid threshold, must be between 2 and $amountMembers"
fi

ValidText_ "Threshold $threshold is OK"

# PORT
echo "-------------------------------------"
read -p "Indicate a new port or press enter for default($port) " aux
if [ -n "$aux" ]; then
    port=$aux
fi

echo "Verifying port $port..."
echo -e "(This step will require administrative privileges)\n"
if sudo netstat -tulpn | grep LISTEN | grep ":$port" > /dev/null 2>&1; then
    LogAndExit_ "Port is in use! You need to specify a different port"
fi

if [[ " ${members[@]} " =~ " ${port} " ]]; then
    LogAndExit_ "Port belongs to a member! You need to specify a different port"
fi

ValidText_ "Port $port is OK"

# NODES
echo "-------------------------------------"
echo -e "Launching nodes\n"
cd "$topDir/Consensus" > /dev/null 2>&1

for m in "${members[@]}"; do
    ./examples/tcp-utils/node.py -id "$m" -p "$port" -t "$threshold" &
    echo "Launched node $m"
done

cd -

# COMMANDER
echo "-------------------------------------"
echo "Launching commander"
echo "To trace the output of the nodes, open another terminal and exec:"
echo -e "\ttail -f $topDir/Consensus/log.txt\n"


"$utilsDir"/cmder.py -p "$port"

wait
