import datetime

import logger
from db import LevelDB
from config import Env
from chain_service import ChainService
import os
import glob
import time
from transactions import Transaction
from keystore import Keystore
from utils import normalize_address
from netaddr import *
import sys
def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

def init_keystore(keys_dir='./keystore/'):
    keys = []
    addresses = []
    for file in glob.glob(os.path.join(keys_dir, '*')):
        key = Keystore.load(keys_dir + file[-40:], "TFG1234")
        keys.append(key)
        addresses.append(normalize_address(key.keystore['address']))
    return keys, addresses

logger.setup_custom_logger('Database')
keys, addresses = init_keystore()
print("Loaded ", len(keys), " keys")
nonce = 0
NUM_TX = 5
NUM_BLOCKS = 100
db = LevelDB("./chain")
env = Env(db)
chain = ChainService(env)
block_creation = []
block_addition = []
for NUM_TX in range(0, 250, 10):
    for j in range(NUM_BLOCKS*2):
        time.sleep(1)
        if j%2 != 0:
            for i in range(1,min(NUM_TX,len(addresses)-1)+1):
                ipset = chain.get_own_ips(addresses[i])
                nonce = chain.chain.state.get_nonce(addresses[i])
                tx = Transaction(nonce, 0, addresses[i-1], 1, ipset.iter_cidrs()[0].ip, time=int(time.time()))
                tx.sign(keys[i].privkey)
                chain.validate_transaction(tx)
                chain.add_pending_transaction(tx)

            c1 = datetime.datetime.now()
            block = chain.create_block(addresses[0])
            block.sign(keys[0].privkey)
            c2 = datetime.datetime.now()
            c3 = c2-c1
            block_creation.append(c3.total_seconds())
            print(sys.getsizeof(block))
            c1 = datetime.datetime.now()
            chain.add_block(block)
            c2 = datetime.datetime.now()
            c3 = c2-c1
            block_addition.append(c3.total_seconds())
            if (NUM_TX != 0):
                nonce = nonce + 1
        else:
            block = chain.create_block(addresses[0])
            block.sign(keys[0].privkey)
            chain.add_block(block)
    print("Data with " +str(NUM_TX) + " Transactions")
    print("Block Creation: " + str(mean(block_creation)))
    print("Block Addition: " + str(mean(block_addition)))