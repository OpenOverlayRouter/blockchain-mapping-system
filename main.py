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


def main():
    end = 0
    chain = init_chain()
    p2p = init_p2p()
    consensus = init_consensus()
    p2p.sync_chain()
    lisp = init_lisp()

    while not end:
        object = select()
        if (isinstance(object, Block)):
            try:
                chain.add_block(object)
            except as e:
                print("error adding block")
                print(e)
        elif (isinstance(object, Transaction)):
            try:
                chain.add_transaction(object)
            except as e:
                print("error adding transaction to pending list")
                print(e)
        elif (isinstance(object, Alocate):  # TODO: completar User_req
            try:
                User_req.create_transaction()
                create_tx(User_req)