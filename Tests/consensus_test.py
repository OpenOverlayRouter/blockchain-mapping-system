import select
import socket
import sys
import Queue
from transactions import Transaction
from block import Block
import chain
import time
from config import Env
from db import LevelDB
from chain_service import ChainService
import select, socket, sys, Queue
import struct
import os
import glob
import rlp
from keystore import Keystore
from consensus import Consensus
from map_reply import MapReplyRecord, LocatorRecord, Response
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

def init_chain():
    db = LevelDB("./chain")
    env = Env(db)
    return ChainService(env)

def init_consensus():
    return Consensus()

if __name__ == "__main__":

    # Consensus Test
    chain = init_chain()
    consensus = init_consensus()

    ks1 = Keystore.load("./Tests/keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")

    tx1 = Transaction(0, 0, "094a2c9f5b46416b959bd9f1efa1f3a73d46cec2", 1, '192.152.0.0/12')
    tx1.sign(ks1.privkey)

    tx8 = Transaction(0, 0, "094a2c9f5b46416b959bd9f1efa1f3a73d46cec2", 2, '2001:cdba::3257:9652')
    tx8.sign(ks1.privkey)

    timestamp = chain.get_head_block().__getattribute__("timestamp")
    block_number = chain.get_head_block().__getattribute__("number")

    consensus.calculate_next_signer(0,timestamp,block_number)
    s = consensus.get_next_signer()
    print s

    while s == None:
        consensus.calculate_next_signer(0,timestamp,block_number)
        s = consensus.get_next_signer()

    block = chain.create_block("094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2")
    block.sign(ks1.privkey)

    block_rlp = rlp.encode(block)
    rlp.decode(block_rlp,Block)

    chain.add_block(block)

    timestamp = chain.get_head_block().__getattribute__("timestamp")
    block_number = chain.get_head_block().__getattribute__("number")

    consensus.calculate_next_signer(0,timestamp,block_number)
    s = consensus.get_next_signer()
    print s

    while s == None:
        consensus.calculate_next_signer(0,timestamp,block_number)
        s = consensus.get_next_signer()
    print s

    try:
        chain.add_pending_transaction(tx1)
        chain.add_pending_transaction(tx8)
    except:
        pass

    block = chain.create_block("094a2c9f5b46416b959bd9f1efa1f3a73d46cec2")
    block.sign(ks1.privkey)

    chain.add_block(block)

    timestamp = chain.get_head_block().__getattribute__("timestamp")
    block_number = chain.get_head_block().__getattribute__("number")

    consensus.calculate_next_signer(0,timestamp,block_number)
    s = consensus.get_next_signer()
    print s

    while s == None:
        consensus.calculate_next_signer(0,timestamp,block_number)
        s = consensus.get_next_signer()
    print s