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

function setupMembers_
{
    owned=($(cat "$utilsDir"/members.txt | grep "$addr" | awk {'print $1'}))
    members=($(cat "$utilsDir"/members.txt | awk {'print $1'}))
    amountMembers=${#members[@]}
    threshold=$((amountMembers/2 + 1))
}

trap "kill 0" EXIT

addr=$(curl https://ipinfo.io/ip)
topDir=$(git rev-parse --show-toplevel)
utilsDir="$topDir/Consensus/examples/tcp-utils"
pport=1111
sport=1112
amountMembers=0
aux=""
isMain=false
if [ "$addr" = "$(cat "$utilsDir"/participants.txt | head -n1)" ]; then
    isMain=true
fi
if [ -f "$utilsDir"/members.txt ]; then
    setupMembers_
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
    setupMembers_
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

# PORTS
echo "-------------------------------------"
read -p "Indicate a new publish port or press enter for default($pport) " aux
if [ -n "$aux" ]; then
    pport=$aux
fi

read -p "Indicate a new subscribe port or press enter for default($sport) " aux
if [ -n "$aux" ]; then
    sport=$aux
fi

ports=($pport $sport)
for port in ${ports[@]}; do
    echo "Verifying port $port..."
    echo -e "(This step will require administrative privileges)\n"
    if sudo netstat -tulpn | grep LISTEN | grep ":$port" > /dev/null 2>&1; then
        LogAndExit_ "Port $port is in use! You need to specify a different port"
    fi

    if [[ " ${owned[@]} " =~ " ${port} " ]]; then
        LogAndExit_ "Port $port belongs to a member! You need to specify a different port"
    fi

    ValidText_ "Port $port is OK"
done

# NODES
echo "-------------------------------------"
echo -e "Launching nodes\n"
cd "$topDir/Consensus" > /dev/null 2>&1

for m in "${owned[@]}"; do
    ./examples/tcp-utils/node.py -id "$m" -p "$pport" -s "$sport" -t "$threshold" &
    echo "Launched node $m"
done

cd -

if $isMain; then

    # BROKER
    echo "-------------------------------------"
    echo "Launching broker"
    "$utilsDir"/broker.py -p "$pport" -s "$sport" &

    # COMMANDER
    echo "-------------------------------------"
    echo "Launching commander"
    echo "To trace the output of the nodes, open another terminal and exec:"
    echo -e "\ttail -f $topDir/Consensus/log.txt\n"

    "$utilsDir"/cmder.py -p "$pport"
    wait

else

    sleep 1
    tail -f "$topDir"/Consensus/log.txt

fi
