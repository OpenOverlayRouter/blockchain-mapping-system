# -*- coding: utf-8 -*-

import select
import socket
import sys
import Queue
from transactions import Transaction
from block import Block
import chain
from config import Env
from db import LevelDB
from chain_service import ChainService
import select, socket, sys, Queue
import struct

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

def run():
    chain = init_chain()
    p2p = init_p2p()
    consensus = init_consensus()
    
    end = 0
    
    while(not end):
        #Process a block
        block = p2p.get_block()
        if block is not None:
            signer = consensus.get_next_signer()
            res = chain.validate_block(block,signer)
            if res:
                # correct block
                myIPs = chain.add_block(block)

                consensus.calculate_next_signer(myIPs)

                p2p.broadcast_block(block)
            else:
            #reset consensus alg
                consensus.calculate_next_signer(None)
    
    #Process transactions from the network
    tx_ext = p2p.get_tx()
    while tx_ext is not None:
        res = chain.validate_transaction(tx_ext)
        if res:
            #correct tx
            chain.add_pending_transaction(tx_ext)
            p2p.broadcast_tx(tx_ext)
        tx_ext = p2p.get_tx()

    
    #Check if the node has to sign the next block
    sign = consensus.amIsinger(myIPs)
    if sign.me is True:
        new_block = chain.create_block(sign.signer)
        p2p.broadcast_block(new_block)
    
    #Process transactions from the user    
    tx_int = user.get_tx()
    if tx_int is not None:
        res = chain.validate_transaction(tx_int)
        if res:
            chain.add_pending_transaction(tx_int)
            p2p.broadcast_tx(tx_int)
    
    #answer queries from OOR     
    query = oor.get_query()
    if query is not None:
        info = chain.query_eid(query)
        oor.send(info)


if __name__ == "__main__":
    init()
    run()
    