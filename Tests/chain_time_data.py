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
NUM_BLOCKS = 50
db = LevelDB("./chain")
env = Env(db)
chain = ChainService(env)
block_creation = []
block_addition = []
for j in range(NUM_BLOCKS*2):
    time.sleep(1)
    if j%2 != 0:
        for i in range(1,min(NUM_TX,len(addresses)-1)+1):
            ipset = chain.get_own_ips(addresses[i])
            if (len(ipset) != 0):
                tx = Transaction(nonce, 0, addresses[i-1], 1, ipset.iter_cidrs()[0].ip, time=int(time.time()))
            else:
                tx = Transaction(nonce, 3, addresses[i], 1, '192.168.0.1', [1, '2.2.2.2', 20, 230, 1, '1.1.1.1', 45, 50])
            tx.sign(keys[i].privkey)
            chain.validate_transaction(tx)
            chain.add_pending_transaction(tx)

        c1 = datetime.datetime.now()
        block = chain.create_block(addresses[0])
        block.sign(keys[0].privkey)
        c2 = datetime.datetime.now()
        c3 = c2-c1
        block_creation.append(c3.total_seconds())

        c1 = datetime.datetime.now()
        chain.add_block(block)
        c2 = datetime.datetime.now()
        c3 = c2-c1
        block_addition.append(c3.total_seconds())
        nonce = nonce + 1
    else:
        block = chain.create_block(addresses[0])
        block.sign(keys[0].privkey)
        chain.add_block(block)


print(block_creation)
print(block_addition)