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
import select, socket, sys, Queue
import struct

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
    # P2P initialization
    return 0

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


class Server():
    def __init__(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        server.bind(('localhost', 50000))
        server.listen(5)
        inputs = [server]
        outputs = []
        message_queues = {}
        while inputs:
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs)
            for s in readable:
                if s is server:
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    message_queues[connection] = Queue.Queue()
                else:
                    # this method reads the amount of bytes indicated by the first 4 bytes of the buffer
                    raw_msglen = recvall(s, 4) # size of data to read
                    if not raw_msglen:
                        print ("error while reading")
                    msglen = struct.unpack('>I', raw_msglen)[0]
                    data = recvall(s, msglen) # read the amount of data indicated by the first 4 bytes
                    print("lo leido es " + str(data))
                    if data:
                        message_queues[s].put(data)
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        del message_queues[s]

            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except Queue.Empty:
                    outputs.remove(s)
                else:
                    s.send(next_msg)

            for s in exceptional:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]


def main():
    pass
    
chain = init_chain()