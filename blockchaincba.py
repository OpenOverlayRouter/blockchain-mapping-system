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

# reads an entire map-request message from the receive socket
def read_socket(rec_socket):
    data = rec_socket.recv(32*6)  # 6 first rows of map-request are fixed
    map_request_message = data
    records = []
    rec_count = int(data[24:32])  # rec_count is located in the bits 24...31 of the map-request message
    for i in range(0, rec_count):
        read = rec_socket.recv(32*2)
        records.append(read)
        map_request_message += read
    map_request_message += rec_socket.recv(32*2)
    return data


'''

    Map-request message format

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Type=1 |A|M|P|S|p|s|    Reserved     |   IRC   | Record Count  |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Nonce . . .                           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         . . . Nonce                           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Source-EID-AFI        |   Source EID Address  ...     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         ITR-RLOC-AFI 1        |    ITR-RLOC Address 1  ...    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                              ...                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         ITR-RLOC-AFI n        |    ITR-RLOC Address n  ...    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 / |   Reserved    | EID mask-len  |        EID-Prefix-AFI         |
Rec +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 \ |                       EID-Prefix  ...                         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                   Map-Reply Record  ...                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   
   '''


def dummy_map_request():
    type = '0'*4
    amps = '0'*4
    reserved = '0'*16
    record_count = '00000003'  # this dummy message will have 3 records
    nonce = '0'*64
    source_eid_afi = '1'*16
    itr_afi = '1'*16
    source_eid_address = '0'*32
    originating_itr_rloc_address = '2'*32

    reserved1 = '0'*8
    eid_mask_len = '00000001'
    eid_prefix_afi = '0'*16
    record1 = reserved1 + eid_mask_len + eid_prefix_afi + '0'*31 + '3'
    record2 = reserved1 + eid_mask_len + eid_prefix_afi + '0'*31 + '4'
    record3 = reserved1 + eid_mask_len + eid_prefix_afi + '0'*31 + '5'

    map_reply_record = '1'*32
    mapping_protocol_data = '2'*32

    map_request_dummy = type + amps + reserved + record_count + nonce + source_eid_afi + itr_afi + source_eid_address +\
        originating_itr_rloc_address + record1 + record2 + record3 + map_reply_record + mapping_protocol_data

    return map_request_dummy


def read_dummy_map_request(map_request):
    first_row = map_request[0:32]
    print(first_row)
    five_rows = map_request[32:32*6]
    for i in range (0, 6):
        print(five_rows[32*i:32*(i+1)])
    rec_count = int(first_row[24:32])
    print("records")
    for i in range (0, rec_count):
        print(map_request[32*(6+i*2):32*(6+i*2+1)])
        print(map_request[32*(7+i*2):32*(7+i*2+1)])


def write_socket(res, snd_socket):
    snd_socket.sendto(res, (HOST, SND_PORT))


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
    read_dummy_map_request(dummy_map_request())
    rec_socket, snd_socket = open_sockets()
    #while 1:
        #write_socket("Hola puto", snd_socket)
        #time.sleep(5)
        #res = read_socket(rec_socket)
        #if res is not None:
            #print(res)
            #write_socket("Respondiendo a..." + str(res), snd_socket)

    #keys = init_keystore()
    #print(keys[0].keystore['address'])

    '''chain = init_chain()
    timestamp = chain.get_head_block().get_timestamp()
    print timestamp
    timestamp = 1511119667

    consensus = init_consensus()
    consensus.calculate_next_signer(0,timestamp)
    print consensus.get_next_signer()

    consensus.calculate_next_signer(0,timestamp)
    print consensus.get_next_signer()'''