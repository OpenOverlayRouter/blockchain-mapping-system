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
members=($(cat "$utilsDir"/members.txt))
amountMembers=${#members[@]}
threshold=$((amountMembers/2 + 1))
port=1111

# MEMBERS
echo "-------------------------------------"
echo "Members are:"
echo "${members[*]}"
ValidText_ "\nThere are $amountMembers members"
echo "(Remember that members are specified in file $utilsDir/members.txt)"

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
    ./examples/tcp-utils/node.py -id "$m" -ids ${members[*]} -p "$port" -t "$threshold" &
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
