from db import LevelDB
from config import Env
from chain_service import ChainService

db = LevelDB("./chain")
env = Env(db)
chain = ChainService(env)
head_block = chain.get_head_block().header.number

print(head_block)

for i in range(head_block):
    block = chain.get_block_by_number(i)
    print ("Asking for block number " + str(i))
    print ("Received block number " + str(block.header.number))