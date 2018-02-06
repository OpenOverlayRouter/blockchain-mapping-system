#import sys
import subprocess
import select
from select import poll, POLLIN
import socket
import messages
import rlp
from transactions import Transaction
from block import Block, BlockHeader
import logging.config

import time

HOST = ''
NOTIFY_PORT = 5005
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
        self.notify = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p = poll()
        self.blocks = False
        self.txs = False
        self.blocks_queries = False
        self.pool_queries = False
    
    def stop(self):
        try:
            self.notify.close()
            self.sock.send(messages.quit())
            self.sock.close()
        except:
            p2pLog.error("P2P stop error")
    
    def start_notifications(self):
        self.notify.connect((HOST, NOTIFY_PORT))
        self.p.register(self.notify, POLLIN)
        #self.notify.setblocking(0)
        end = False
        buffer = ''
        while not end:
            rlist, _, _ = select.select([self.notify], [], [])
            if rlist:
                buffer += self.notify.recv(4096)
                if buffer[-2:] == "\r\n":
                    for data in buffer.split("\r\n"):
                        if data == '0':
                            self.blocks = True
                        elif data == '1':
                            self.txs = True
                        elif data == '2':
                            self.blocks_queries = True
                        elif data == '3':
                            self.pool_queries = True
                    end = True
    
    def data_avalaible(self):
        try:
            rlist = self.p.poll(100)
            if rlist:
                buffer = self.notify.recv(4096)
                if buffer:
                    while not buffer[-2:] == "\r\n":
                        buffer += self.notify.recv(4096)
                    for data in buffer.split("\r\n"):
                            if data == '0':
                                self.blocks = True
                            elif data == '1':
                                self.txs = True
                            elif data == '2':
                                self.blocks_queries = True
                            elif data == '3':
                                self.pool_queries = True
        except:
            pass

    
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
            if not self.txs:
                self.data_avalaible()
            if self.txs:
                self.sock.send(messages.get_tx())
                data = self.read()
                if data["msgtype"] == "none":
                    self.txs = False
                    return None
                else:
                    tx = rlp.decode(data["tx"].decode('base64'), Transaction)
                    return tx
            else:
                return None
        except:
            p2pLog.error("P2P get_tx error")

    def broadcast_tx(self, tx):
        try:
            self.sock.send(messages.set_tx(tx))
        except:
            p2pLog.error("P2P broadcast_tx error")

    def get_block(self):
        try:
            if not self.blocks:
                self.data_avalaible()
            if self.blocks:
                self.sock.send(messages.get_block())
                data = self.read()
                if data["msgtype"] == "none":
                    self.blocks = None
                    return None
                else:
                    block = rlp.decode(data["block"].decode('base64'), Block)
                    return block
            else:
                return None
        except:
            p2pLog.error("P2P get_block error")

    def broadcast_block(self, block):
        try:
            self.sock.send(messages.set_block(block))
            p2pLog.info("Block no. %s sent successfully to the network.", block.header.number)
        except:
            p2pLog.error("P2P broadcast_block error")
    
    def get_block_queries(self):
        try:
            if not self.blocks_queries:
                self.data_avalaible()
            if self.blocks_queries:
                self.sock.send(messages.get_block_queries())
                data = self.read()
                if data["msgtype"] == "none":
                    self.blocks_queries = False
                    return None
                else:
                    return data["blocks"]
            else:
                return None
        except:
            p2pLog.error("P2P get_block_queries error")
    
    def answer_block_queries(self, response):
        try:
            self.sock.send(messages.answer_block_queries(response))
        except:
            p2pLog.error("P2P answer_block_queries error")
    
    def tx_pool_query(self):
        try:
            if not self.pool_queries:
                self.data_avalaible()
            if self.pool_queries:
                self.sock.send(messages.tx_pool_query())
                data = self.read()
                if data["msgtype"] == "true":
                    return True
                else:
                    self.pool_queries = False
                    return False
            else:
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
