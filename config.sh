#!/bin/bash
# Installation of python dependencies to run blockchaincba.py
#pass the vm location as the first parameter

location=$1

sudo apt update
sudo apt upgrade
echo "Performing language adjustments"
sudo apt-get -y install language-pack-en-base
sudo apt-get -y install language-pack-ca-base

sudo dpkg-reconfigure locales

sudo apt-get -y install ntp
sudo ntpq -p

#echo "Creating blockchain repo"
#mkdir blockchain-repo
#cd blockchain-repo
#git init
#git clone https://github.com/CodeEaterX/blockchain
#git checkout dht-tests


echo "Installing all dependencies"
sudo apt-get -y install python
sudo apt-get -y install python-scrypt
sudo apt-get -y install python-pip
sudo apt-get -y install libgmp-dev libssl-dev
sudo pip install --upgrade pip
sudo pip install py_ecc==1.1.3
sudo pip install rlp==0.6.0
sudo pip install PyCryptodome
sudo pip install netaddr
sudo pip install ipaddr
sudo pip install ipaddress
sudo pip install leveldb
sudo pip install bitcoin
sudo pip install twisted
sudo pip install pytricia
sudo pip install bitstring
sudo pip install py-radix
sudo pip install psutil
sudo pip install -I kademlia==0.6 rpcudp==2.0
cd libs/ipgetter-master/
sudo python setup.py install
cd ../..

#Compile BLS.exe
./Consensus/getDependencies.sh

#Give execution permission to the BLS executable
chmod 744 Consensus/utils/bls.exe
echo "Adjusting keystore and transactions for location" $location
#rm -r keystore
mv dataset/keystores/keystore-$location keystore
mv dataset/transactions/$location-transactions.txt transactions.txt


echo "Done :)"

echo "Remember to select the appropriate keys & transactions folders before booting this node!"


#sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

#OOR modificat per blockchain és a 
#https://github.com/MiquelFerriol/OOR_CBA
#seguir instruccions readme:
#1)instal·lar paquets
#2)compilar
#OOR:
#sudo oor -d 3 -f oor/oor_mr.conf
#El sudo no és necessari, pero lleva algún warning que fa que el log sigui una mica engorrós...

#ubicació LIG
#https://github.com/LISPmob/lig-lispmob


# Config lig
#git clone https://github.com/LISPmob/lig-lispmob.git git
#cd git/
#make
#sudo cp ./lig /usr/sbin/
#executar sempre des d'una altra màquina que la del MapResovler
#lig -m <IP MapResolver> -p 4342 -s <IP maquina local> <EID a consultar (una IP)>
#

