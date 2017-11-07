import select
import socket
import sys
import Queue
from transactions import Transaction
from block import Block
import chain_service
from config import Env
from db import LevelDB
from chain_service import ChainService
import asyncore, socket

inputs = []
outputs = []


def init_chain():
    db = LevelDB("./chain")
    env = Env(db)
    return ChainService(env)


def init_p2p():
    # P2P initialization
    return 0


def init_consensus():
    # Consensus initialization
    return 0

def init_lisp():
    # LISP initialization
    return 0

class Server(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', port))
        self.listen(1)

    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        socket, address = self.accept()
        print 'Connection by', address
        EchoHandler(socket)

class EchoHandler(asyncore.dispatcher_with_send):
    # dispatcher_with_send extends the basic dispatcher to have an output
    # buffer that it writes whenever there's content
    def handle_read(self):
        self.out_buffer = self.recv(1024)
        if not self.out_buffer:
            self.close()


def main():
    end = 0
    chain = init_chain()
    p2p = init_p2p()
    consensus = init_consensus()
    p2p.sync_chain()
    lisp = init_lisp()

    s = Server('', 5007)
    asyncore.loop()
