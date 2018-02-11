#import sys
import subprocess
import select
import socket
import messages
import rlp
from transactions import Transaction
from block import Block, BlockHeader
import logging.config

import time

HOST = ''
QUERY_PORT = 5006

p2pLog = logging.getLogger('P2P')

class P2P():

    def __init__(self, last_block):
        #self.p = subprocess.Popen([sys.executable, "network.py", last_block, ip])
        self.p = subprocess.Popen(["nohup", "python", "network.py", str(last_block)],
                                  stdout=open('network.out', mode='w+', buffering=0), shell=False)
        time.sleep(5)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, QUERY_PORT))
        #self.sock.setblocking(0)
    
    def stop(self):
        try:
            self.sock.send(messages.quit())
            self.sock.close()
        except:
            p2pLog.error("P2P stop error")
    
    def read(self):
        buffer = ''
        while True:
            rlist, _, _ = select.select([self.sock], [], [])
            if rlist:
                buffer += self.sock.recv(4096)
                if buffer[-2:] == "\r\n":
                    return messages.read_envelope(buffer.strip())

    def bootstrap(self):
        try:
            self.sock.send(messages.bootstrap())
            data = self.read()
            if data["msgtype"] == "true":
                return True
            else:
                return False
        except:
            p2pLog.error("P2P bootstrap error")
    
    def get_tx(self):
        try:
            self.sock.send(messages.get_tx())
            data = self.read()
            if data["msgtype"] == "none":
                self.txs = False
                return None
            else:
                tx = rlp.decode(data["tx"].decode('base64'), Transaction)
                return tx
        except:
            p2pLog.error("P2P get_tx error")

    def broadcast_tx(self, tx):
        try:
            self.sock.send(messages.set_tx(tx))
        except:
            p2pLog.error("P2P broadcast_tx error")

    def get_block(self):
        try:
            self.sock.send(messages.get_block())
            data = self.read()
            if data["msgtype"] == "none":
                self.blocks = None
                return None
            else:
                block = rlp.decode(data["block"].decode('base64'), Block)
                return block
        except:
            p2pLog.error("P2P get_block error")

    def broadcast_block(self, block):
        try:
            self.sock.send(messages.set_block(block))
        except:
            p2pLog.error("P2P broadcast_block error")
    
    def get_block_queries(self):
        try:
            self.sock.send(messages.get_block_queries())
            data = self.read()
            if data["msgtype"] == "none":
                self.blocks_queries = False
                return None
            else:
                return data["blocks"]
        except:
            p2pLog.error("P2P get_block_queries error")
    
    def answer_block_queries(self, response):
        try:
            self.sock.send(messages.answer_block_queries(response))
        except:
            p2pLog.error("P2P answer_block_queries error")
    
    def tx_pool_query(self):
        try:
            self.sock.send(messages.tx_pool_query())
            data = self.read()
            if data["msgtype"] == "true":
                return True
            else:
                self.pool_queries = False
                return False
        except:
            p2pLog.error("P2P tx_pool_query error")

    def answer_tx_pool_query(self, pool):
        try:
            self.sock.send(messages.answer_tx_pool_query(pool))
        except:
            p2pLog.error("P2P answer_tx_pool_query")

if __name__ == '__main__':
    pass
