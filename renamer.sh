


if [ "$#" -ne 3 ];then
  echo "Usage: bash log_renamer.sh <node> <date> <version>"
  exit 1
fi

node=$1
day=$2
version=$3


mv -i log.txt log-$node-$day-$version.txt
mv -i network.out network-$node-$day-$version.out
mv -i delays-process-block.txt delays-process-block-$node-$day-$version.txt
mv -i delays-create-txs.txt delays-create-txs-$node-$day-$version.txt
