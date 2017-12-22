import rlp
from transactions import Transaction
from block import Block, BlockHeader
from p2p import P2P

import time
import sys


blocks = {}
num_blocks = 0
tx_pool = []


def gen_blocks(n):
    global blocks, num_blocks
    block = Block(BlockHeader(timestamp=int(time.time())))
    blocks[0] = block
    for i in range(n):
        b = Block(BlockHeader(timestamp=int(time.time()), prevhash=blocks[i].hash, number=blocks[i].header.number + 1))
        blocks[i+1] = b
        num_blocks += 1

def gen_tx_pool():
    global tx_pool
    tx = Transaction(5,3,'54450450e24286143a35686ad77a7c851ada01a0', 2, '2001:db8::1/16', [2, '2001:cdba:9abc:5678::', 20, 230])
    tx_pool.append(tx)

if __name__ == '__main__':
    gen_blocks(100)
    gen_tx_pool()
    p2p = P2P(num_blocks)
    while (p2p.bootstrap()):
        pass
    p2p.start_notifications()
    #start = time.time()
    end = False
    while not end:
        # Process Block
        #print "Process Block"
        try:
            block = p2p.get_block()
            while block is not None:
                blocks[block.header.number] = block
                print block.header.number
                block = p2p.get_block()
        except Exception as e:
            print "Exception while processing a received block"
            print e
        # Process Tx
        #print "Process Tx"
        try:
            tx_ext = p2p.get_tx()
            while tx_ext is not None:
                print rlp.encode(tx_ext).encode('hex')
                tx_ext = p2p.get_tx()
        except Exception as e:
            print "Exception while processing a received transaction"
            print e
        #answer queries from the network
        #blocks
        #print "Get Block Queries"
        try:
            block_numbers = p2p.get_block_queries()
            if block_numbers is not None:
                print "Block Queries", block_numbers
                response = []
                for block in block_numbers:
                    response.append(blocks.get(block))
                p2p.answer_block_queries(response)
        except Exception as e:
            print "Exception while answering blocks"
            print e
        #transaction pool
        #print "Get Tx Pool Query"
        try:
            if p2p.tx_pool_query():
                print "Pool Query"
                pool = tx_pool
                p2p.answer_tx_pool_query(pool)
        except Exception as e:
            print "Exception while answering pool"
            print e
        '''if time.time() - start >= 100:
            p2p.stop()
            end = True'''
        
