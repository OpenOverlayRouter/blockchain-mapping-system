# -*- coding: utf-8 -*-

import select
import socket
import sys
import Queue

from netaddr import IPNetwork

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
from map_reply import MapReplyRecord, LocatorRecord, Response, MapServers
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from netaddr import IPAddress
from p2p import P2P
import sys
import socket
import fcntl, os
import errno
from time import sleep
import logging
import logging.config
import logger
from user import Parser
from utils import normalize_address

mainLog = logging.getLogger('Main')


def init_chain():
    db = LevelDB("./chain")
    env = Env(db)
    return ChainService(env)


def init_p2p(last_block_num):
    # P2P initialization
    p2p = P2P(last_block_num)
    while (p2p.bootstrap()):
        time.sleep(1)
    p2p.start_notifications()
    return p2p


def init_consensus():
    return Consensus()


def init_user():
    return Parser()


def init_keystore(keys_dir='./Tests/keystore/'):
    keys = []
    addresses = []
    for file in glob.glob(os.path.join(keys_dir, '*')):
        key = Keystore.load(keys_dir + file[-40:], "TFG1234")
        keys.append(key)
        addresses.append(normalize_address(key.keystore['address']))
    return keys, addresses


def init_logger():
    logger.setup_custom_logger('Main')
    logger.setup_custom_logger('Database')
    logger.setup_custom_logger('P2P')
    logger.setup_custom_logger('OOR')
    logger.setup_custom_logger('Consensus')
    logger.setup_custom_logger('Parser')


def run():
    init_logger()

    mainLog.info("Initializing Chain")
    chain = init_chain()

    mainLog.info("Initializing P2P")
    p2p = init_p2p(chain.get_head_block().header.number)

    mainLog.info("Initializing Consensus")
    consensus = init_consensus()

    mainLog.info("Initializing Keystore")
    keys, addresses = init_keystore()

    mainLog.info("Initializing Parser")
    user = init_user()

    end = 0
    myIPs = chain.get_own_ips(keys[0].address)
    block_num = chain.get_head_block().header.number
    timestamp = chain.get_head_block().header.timestamp
    consensus.calculate_next_signer(myIPs, timestamp, block_num)

    while(not end):
        #Process new blocks
        try:
            block = p2p.get_block()
            while block is not None:
                signer = consensus.get_next_signer() 
                res = chain.verify_block_signature(block, signer)
                if res:
                    # correct block
                    chain.add_block(block)
                    myIPs = chain.get_own_ips(keys[0].address)
                    timestamp = chain.get_head_block().get_timestamp()
                    block_num = chain.get_head_block().header.number
                    consensus.calculate_next_signer(myIPs, timestamp, block_num)
                block = p2p.get_block()
        except Exception as e:
            mainLog.critical("Exception while processing a received block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)
    
        #Process transactions from the network
        try:
            tx_ext = p2p.get_tx()
            while tx_ext is not None:
                try:
                    chain.add_pending_transaction(tx_ext)
                    # Correct tx
                    p2p.broadcast_tx(tx_ext)
                except:
                    pass
                #get new transactions to process
                tx_ext = p2p.get_tx()
        except Exception as e:
            mainLog.critical("Exception while processing a received transaction")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)


        #Check if the node has to sign the next block
        try:
            me, signer = consensus.amISigner(myIPs, block_num)
            if me:
                new_block = chain.create_block(keys[0].address)
                #Like receiving a new block
                chain.add_block(new_block)
                #Revisar
                p2p.broadcast_block(new_block)
            myIPs = chain.get_own_ips(keys[0].address)
            timestamp = chain.get_head_block().header.timestamp
            block_num = chain.get_head_block().header.number
            consensus.calculate_next_signer(myIPs, timestamp, block_num)
        except Exception as e:
            mainLog.critical("Exception while checking if the node has to sign the next block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        # Process transactions from the user
        try:
            user.read_transactions()
            tx_int = user.get_tx()
            if tx_int is not None:
                try:
                    try:
                        key = addresses.index(tx_int["from"])
                    except:
                        raise Exception("Key indicated in from field is not in present in the keystore")
                    key = keys[key]
                    tx = chain.parse_transaction(tx_int)
                    tx.sign(key.privkey)
                    # correct tx
                    p2p.broadcast_tx(tx)
                except:
                    pass
        except Exception as e:
            print "Exception while processing transactions from the user"
            print e
            p2p.stop()
            sys.exit(0)

        #answer queries from OOR
        '''try:
            query = oor.get_query()
            if query is not None:
                info = chain.query_eid(query)
                oor.send(info)
        except Exception as e:
            mainLog.critical("Exception while answering queries from OOR")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)'''

        #answer queries from the network
        #blocks
        try:
            block_numbers = p2p.get_block_queries()
            if block_numbers is not None:
                response = []
                for block in block_numbers:
                    response.append(chain.get_block(block))
                p2p.answer_block_queries(response)
        except Exception as e:
            mainLog.critical("Exception while answering queries from the network")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)             

            
        #transaction pool
        try:
            if p2p.tx_pool_query():
                pool = chain.get_pending_transactions()
                p2p.answer_tx_pool_query(pool)
        except Exception as e:
            mainLog.critical("Exception while answering the transaction pool")
            mainLog.exception(e)
            # Stop P2P
            p2p.stop()
            sys.exit(0)

if __name__ == "__main__":
    #filename = '.log/blockchainCBA.log',
    #filemode = 'w'
    # create logger

    run()

    """
    keys = init_keystore()
    chain = init_chain()
    chain.query_eid(keys[0].keystore['address'], IPv4Address('192.168.0.1'))
    """
    rec_socket, snd_socket = open_sockets()
    fcntl.fcntl(rec_socket, fcntl.F_SETFL, os.O_NONBLOCK)
    fcntl.fcntl(snd_socket, fcntl.F_SETFL, os.O_NONBLOCK)
    while 1:
        read_request_and_process()
        print("HOLA")
        """
        res = rec_socket.recvfrom(50)[0]
        if res is not None:
            print(struct.pack('>I',(int(struct.unpack("I",res[0:4])[0]))).encode('HEX'))
            print(struct.pack('>I',(int(struct.unpack("I",res[4:8])[0]))).encode('HEX'))
            afi = int(struct.unpack("H",res[8:10])[0])
            if afi == 1:
                ip = IPv4Address(res[18:])
                print(ip)
            elif afi == 2:
                ip = IPv6Address(res[18:])
                print(ip)
            msg = struct.pack('>I',(int(struct.unpack("I",res[0:4])[0]))) + struct.pack('>I',(int(struct.unpack("I",res[4:8])[0]))) + struct.pack('H',int(struct.unpack("H",res[8:10])[0]))
            write_socket(msg,snd_socket)"""

        time.sleep(0.5)
