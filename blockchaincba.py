# -*- coding: utf-8 -*-


import sys


#from netaddr import IPNetwork

#from transactions import Transaction
#from block import Block
#import chain
import time
from config import Env
from db import LevelDB
from chain_service import ChainService

import os
import glob
#import rlp
from keystore import Keystore
from consensus import Consensus

from netaddr import IPSet
from p2p import P2P

import logging
import logging.config
import logger
from user import Parser
from utils import normalize_address
from oor import Oor

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
    mainLog.info("Bootstrap finished")
    p2p.start_notifications()
    return p2p


def init_consensus():
    return Consensus()


def init_user():
    return Parser()


def init_keystore(keys_dir='./keystore/'):
    keys = []
    addresses = []
    for file in glob.glob(os.path.join(keys_dir, '*')):
        key = Keystore.load(keys_dir + file[-40:], "TFG1234")
        print ("key %s loaded from %s", key, file)
        keys.append(key)
        addresses.append(normalize_address(key.keystore['address']))
    return keys, addresses

def init_oor():
    return Oor()


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


    last_block = chain.get_head_block().header.number
    mainLog.debug("Last block: %s", last_block)
    mainLog.info("Initializing P2P")
    p2p = init_p2p(chain.get_head_block().header.number)

    mainLog.info("Initializing Consensus")
    consensus = init_consensus()

    mainLog.info("Initializing Keystore")
    keys, addresses = init_keystore()
    mainLog.info("Loaded %s keys", len(keys))
    mainLog.info("----------------START OF KEY LIST---------------------")
    print keys
    print addresses
    mainLog.info("----------------END OF KEY LIST---------------------")
    
    mainLog.info("Initializing Parser")
    user = init_user()
    user.read_transactions()

    mainLog.info("Initializing OOR")
    oor = init_oor()

    end = 0
    myIPs = IPSet()
    for i in range(len(keys)):
        myIPs.update(chain.get_own_ips(keys[i].address))
    mainLog.info("Own IPs at startup are: %s", myIPs)
    
    block_num = chain.get_head_block().header.number
    timestamp = chain.get_head_block().header.timestamp
    consensus.calculate_next_signer(myIPs, timestamp, block_num)
    

    while(not end):
        #Process new blocks
        try:
            block = p2p.get_block()
            while block is not None:
                mainLog.info("Received new block no. %s", block.number)
                signer = consensus.get_next_signer() 
                res = chain.verify_block_signature(block, signer)
                if res:
                    # correct block
                    chain.add_block(block)
                    myIPs = IPSet()
                    for i in range(len(keys)):
                        myIPs.update(chain.get_own_ips(keys[i].address))
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
                mainLog.info("This node has to sign a block")
                signing_addr = chain.get_addr_from_ip(signer)
                #new_block = chain.create_block(keys[0].address)
                new_block = chain.create_block(signing_addr)
                mainLog.info("Created new block no. %s, timestamp %s, coinbase %s", \
                    new_block.header.number, new_block.header.timestamp, new_block.header.coinbase)
                mainLog.info("New block signature data: v %s -- r %s -- s %s", new_block.v, new_block.r, new_block.s)
                #Like receiving a new block
                chain.add_block(new_block)
                #Revisar
                p2p.broadcast_block(new_block)
                myIPs = IPSet()
                for i in range(len(keys)):
                    myIPs.update(chain.get_own_ips(keys[i].address))            
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
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        #answer queries from OOR
        try:
            nonce, afi, address = oor.get_query()
            if nonce is not None and afi is not None and address is not None:
                info = chain.query_eid(ipaddr=address, nonce=nonce)
                oor.send(info)
        except Exception as e:
            mainLog.critical("Exception while answering queries from OOR")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        #answer queries from the network
        #blocks
        try:
            block_numbers = p2p.get_block_queries()
            if block_numbers is not None:
                mainLog.info("Answering query for block nos. %s", block_numbers)
                response = []
                for block in block_numbers:
                    response.append(chain.get_block_by_number(block))
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
