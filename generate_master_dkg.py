#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 14:30:49 2019

@author: jordip
"""


import sys
import hashlib
import consensus
import utils

DKG_NUMBER_PARTICIPANTS = 100

#Make the random selection
random_no = utils.compress_random_no_to_int('0xabff75259697c051af1299ce30dc74a108ff5d6bbcc24bb2c8c5dfa8864fa41f', 16)
random_no_string = '0xabff75259697c051af1299ce30dc74a108ff5d6bbcc24bb2c8c5dfa8864fa41f'

#Load master addresses        
#List all addresses at the moment in the chain
all_addresses = []
try:    
    all_addr = open('dataset/master-all-addrs-db-order.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
for line in all_addr:
    all_addresses.append(line.rstrip('\n'))
all_addr.close()


#Randomly select participants from all the addresses
dkg_group = []
for i in range(DKG_NUMBER_PARTICIPANTS):
    random_pos = random_no % len(all_addresses)
    dkg_group.append(utils.normalize_address(all_addresses.pop(random_pos)))
    random_no = utils.compress_random_no_to_int(hashlib.sha256(str(random_no)).hexdigest(), 16)

print "Selected the following addresses for the DKG:"
for elem in dkg_group:
    print elem.encode('hex')

#Generate DKG shares
cons = consensus.Consensus(dkg_group, dkg_group, random_no_string, 0x00, 0)
to_send = cons.new_dkg(dkg_group, dkg_group)
#Since we have given him all nodes, we can join the DKG shares directly

if cons.all_node_dkgs_finished():
    print "Group key is: ", cons.get_current_group_key()
    print "Now writing private keys in file"
else:
    print "Fatal error, we own all nodes, DKG should be finished. Exiting"
    sys.exit(1)
        
#Store private keys in file
try:    
    priv_keys = open('master-private-dkg-keys.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
for node in dkg_group:
    oid = node
    secretkey = cons.secretKeys[oid]
    priv_keys.write(oid.encode('hex') + ' ' + secretkey + '\n')
    
priv_keys.close()
print "Done"
