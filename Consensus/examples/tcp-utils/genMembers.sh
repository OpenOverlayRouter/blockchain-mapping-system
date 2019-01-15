#!/bin/bash
set -euo pipefail

function usage_
{
    echo "Usage: $0 <min> <max> <amount>"
    echo "\t <min>: Lowest id that can be generated"
    echo "\t <max>: Highest id that can be generated"
    echo "\t <amount>: Amount of ids that will be generated"
}

genDir=$(dirname $0)
membersFile="$genDir"/members.txt
participants=($(cat "$genDir"/participants.txt))
numParticipants=${#participants[@]}

if [ $# -ne 3 ]; then
    usage_
fi

if [ -f "$membersFile" ]; then
    rm "$membersFile"
fi

members=($(shuf -i "$1"-"$2" -n "$3"))

for (( i=0; i<$3; i++ )); do
    owner=${participants[$(( $i % $numParticipants ))]}
    echo "${members[i]} $owner" >> "$membersFile"
done

