import sys
sys.path.append("/home/blockchain/blockchain")
sys.path.append("/home/blockchain/blockchain/Tests")
from db import LevelDB
from config import Env
from chain_service import ChainService

db = LevelDB("./chain")
env = Env(db)

chain = ChainService(env)
head_block = chain.get_head_block().header.number

print(head_block)

for k in db.db.RangeIter(include_value = False):
    print "Key", k
    print "Encoded key", k.encode('HEX')

for i in range(head_block):
    block = chain.get_block_by_number(i)
    print ("Asking for block number " + str(i))
    print ("Received block number " + str(block.header.number))