#!/bin/bash
EXEC_TIMES=100
start_time=`date +%s%N`
for i in $(seq 1 $EXEC_TIMES);
do
   echo "Welcome $i times"
done
echo run time is $(expr `date +%s%N` - $start_time) ns