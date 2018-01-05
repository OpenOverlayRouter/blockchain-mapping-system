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
print(chain.get_head_block().header.prevhash.encode("HEX"))
print(head_block)

for i in range(0,head_block+1):
    block = chain.get_block_by_number(i)
    print ("Asking for block number " + str(i))
    print ("Received block number " + str(block.header.number))
    print ("Received block hash " + str(block.hash.encode("HEX")))
    print ("Received prevhash " + str(block.header.prevhash.encode("HEX")))