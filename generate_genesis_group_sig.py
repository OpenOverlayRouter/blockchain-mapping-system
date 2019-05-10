# -*- coding: utf-8 -*-
"""
Created on Thu May  9 13:44:09 2019

@author: jordi
"""
import sys
import consensus as cons
import utils, logger

from config import Env
from db import LevelDB
from chain_service import ChainService

logger.setup_custom_logger('Consensus')
logger.setup_custom_logger('Database')

prev_rand_no = 'fab206a4186845ff0f0192fd06be977971a7dedbf9c22173cc38d23625aac2a7'


print "load chain"
db = LevelDB("./chain")                                                                                                                                                                                                                                                    
env = Env(db)
chain = ChainService(env)

block_num = chain.get_head_block().header.number
current_random_no = chain.get_head_block().header.random_number.encode('hex')
current_group_key = chain.get_current_group_key()
dkg_group = chain.get_current_dkg_group()

if current_random_no != prev_rand_no:
    print "error, block rand no is not the specified one!!!!!!"
    sys.exit(0)

print "init consensus"
consensus = cons.Consensus(dkg_group, dkg_group, current_random_no, current_group_key, block_num, "0x00")





print "Manual force of priv_keys"
try:
    priv_keys = open('master-private-dkg-keys.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

print "Detected master private key file. Perfoming manual setup of DKG private keys."
sec_keys = {}
for line in priv_keys:
    content = line.split(' ')
    sec_keys[utils.normalize_address(content[0])] = content[1].rstrip('\n')        
priv_keys.close()

try:
    consensus.bootstrap_master_add_secret_keys_manual(sec_keys)
    consensus.verified = False
    print "create shares and sig"
    
    consensus.create_shares(block_num)
    print "group sig is"
    print consensus.group_sig
except Exception as e: 
    print e
    sys.exit(1)
    
print "Try to verify this sig"
expected_message = str(current_random_no) + str(0) + str(0) 
print consensus.bootsrap_verify_group_sig(expected_message, consensus.group_sig)
