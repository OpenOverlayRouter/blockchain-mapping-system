#!/bin/bash
set -euo pipefail

function usage_
{
    echo "Usage: $0 <min> <max> <amount>"
    echo "\t <min>: Lowest id that can be generated"
    echo "\t <max>: Highest id that can be generated"
    echo "\t <amound>: Amount of ids that will be generated"
}

genDir=$(dirname $0)


if [ $# -ne 3 ]; then
    usage_
fi

shuf -i "$1"-"$2" -n "$3" > "$genDir"/members.txt

