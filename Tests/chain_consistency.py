from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from db import _EphemDB
from block import Block, BlockHeader
import time
import transactions
import trie
import rlp
import state
from utils_test import get_rand_tx
from db import LevelDB,_EphemDB
import time
from transactions import Transaction
import copy
from db import _EphemDB
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
from chain_service import ChainService
import sys

db = LevelDB("./chain")
env = Env(db)
chain = ChainService(env)
head_block = chain.get_head_block().header.number

print(head_block)

for i in range(head_block):
    block = chain.get_block_by_number(i)
    print ("Asking for block number " + str(i))
    print ("Received block number " + str(block.header.number))