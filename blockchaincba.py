# -*- coding: utf-8 -*-

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
from keystore import Keystore
from consensus import Consensus
from map_reply import MapReplyRecord, LocatorRecord
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

HOST = ''
REC_PORT = 16001
SND_PORT = 16002


def open_sockets():
    try:
        rec_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        snd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print 'Socket created'
    except socket.error, msg:
        print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit(1)
    # Bind socket to local host and port
    try:
        rec_socket.bind((HOST, REC_PORT))
    except socket.error:
        print 'Bind failed.'
        sys.exit(1)

    print 'Socket bind complete in ports ' + str(REC_PORT) + ' and ' + str(SND_PORT)

    return rec_socket, snd_socket


# reads the fields nonce, AFI and the IP from the socket
def read_socket(rec_socket):
    nonce = rec_socket.recv(6)
    print("nonce")
    print(nonce)
    afi = rec_socket.recv(1)
    print("afi")
    print(afi)
    if (afi == '1'):
        # address IPv4
        address = IPv4Address(rec_socket.recv(32))
    elif (afi == '2'):
        # address IPv6
        address = IPv6Address(rec_socket.recv(128))
    else:
        rec_socket.recv(1024)  # used to empty socket
        raise Exception('Incorrect AFI read from socket')
    return nonce, afi, address


def write_socket(res, snd_socket):
    snd_socket.sendto(res, (HOST, SND_PORT))


def test_map_reply():
    locator = LocatorRecord(priority=0, weight=0, mpriority=0, mweight=0, unusedflags=0, LpR=0,
                            locator=IPv4Address("192.168.0.1"))
    locators = []
    locators.append(locator)
    reply = MapReplyRecord(eid_prefix=IPv4Network(u'192.168.1.0/24'), locator_records=locators)
    print(reply.to_bitstream())


def init_chain():
    db = LevelDB("./chain")
    env = Env(db)
    return ChainService(env)


def init_p2p():
    # P2P initialization
    return 0


def init_consensus():
    return Consensus()


def init_keystore(keys_dir='./Tests/keystore/'):
    keys = []
    for file in glob.glob(os.path.join(keys_dir, '*')):
        keys.append(Keystore.load(keys_dir + file[-40:], "TFG1234"))
    return keys


def run():
    chain = init_chain()
    p2p = init_p2p()
    consensus = init_consensus()
    keys = init_keystore()
    end = 0

    while(not end):
        
        #Process a block from the network
        try:
            block = p2p.get_block()
            if block is not None:
                signer = consensus.get_next_signer()
                res = chain.verify_block_signature(block, signer)
                if res:
                    # correct block
                    consensus.store_block(block)
                    #Maybe not necessary, depends on P2P implementation
                    p2p.broadcast_block(block)
                else:
                    #reset consensus alg
                    consensus.calculate_next_signer(None)
        except Exception as e:
            print "Exception while processing a received block"
            print e
     
        #Process a definitive block
        try:
            block = consensus.get_solid_block()
            if block is not None:
                #These blocks are always OK
                #Only needed to validate tx logic (apply.py)
                #For simplicity we assume that the previous validation will never fail
                myIPs = chain.add_block(block)
                timestamp = chain.get_head_block().get_timestamp()
                consensus.calculate_next_signer(myIPs, timestamp)
        except Exception as e:
            print "Exception while adding a definitive block"
            print e

        #Process transactions from the network
        try:
            tx_ext = p2p.get_tx()
            while tx_ext is not None:
                res = chain.add_pending_transaction(tx_ext)
                if res:
                    #correct tx
                    p2p.broadcast_tx(tx_ext)
                #get new transactions to process
                tx_ext = p2p.get_tx()
        except Exception as e:
            print "Exception while processing a received transaction"
            print e


        #Check if the node has to sign the next block
        sign = consensus.amIsinger(myIPs)
        if sign.me is True:
            last_block_hash = consensus.get_last_block_hash()
            #TODO: Do you need transactions in the previous blocks (unconfirmed)? I think so :(
            new_block = chain.create_block(sign.signer,last_block_hash)
            consensus.store_block(new_block)
            p2p.broadcast_block(new_block)

        #Process transactions from the user
        tx_int = user.get_tx()
        if tx_int is not None:
            res = chain.add_pending_transaction(tx_int)
            if res:
                #correct tx
                p2p.broadcast_tx(tx_int)

        #answer queries from OOR
        query = oor.get_query()
        if query is not None:
            info = chain.query_eid(query)
            oor.send(info)


if __name__ == "__main__":
    #init()
    #run
    #test_map_reply()
    #keys = init_keystore()
    #chain = init_chain()
    #chain.query_eid(keys[0].keystore['address'], IPv4Address("192.168.0.1"))
    rec_socket, snd_socket = open_sockets()
    while 1:
        #write_socket("Hola puto", snd_socket)
        #time.sleep(5)
        res = read_socket(rec_socket)
        if res is not None:
            print(res)
            #write_socket("Respondiendo a..." + str(res), snd_socket)



    '''chain = init_chain()
    timestamp = chain.get_head_block().get_timestamp()
    print timestamp
    timestamp = 1511216597

    consensus = init_consensus()
    consensus.calculate_next_signer(0,timestamp)
    print consensus.get_next_signer()

    consensus.calculate_next_signer(0,timestamp)
    print consensus.get_next_signer()'''