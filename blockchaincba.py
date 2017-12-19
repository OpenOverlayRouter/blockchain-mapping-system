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
from p2p import P2P
import sys
import fcntl, os
from oor import Oor
from user import Parser
from utils import normalize_address


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


def init_keystore(keys_dir='./Tests/keystore/'):
    keys = []
    addresses = []
    for file in glob.glob(os.path.join(keys_dir, '*')):
        key = Keystore.load(keys_dir + file[-40:], "TFG1234")
        keys.append(key)
        addresses.append(normalize_address(key.keystore['address']))
    return keys, addresses


def init_oor():
    return Oor()

def init_user():
    return Parser()

def run():
    chain = init_chain()
    p2p = init_p2p(chain.get_head_block().header.number)
    consensus = init_consensus()
    keys, addresses = init_keystore()
    end = 0
    myIPs = chain.get_own_ips(keys[0].address)
    block_num = chain.get_head_block().header.number
    timestamp = chain.get_head_block().header.timestamp
    consensus.calculate_next_signer(myIPs, timestamp, block_num)
    oor = init_oor()
    user = init_user()

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
            print "Exception while processing a received block"
            print e
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
            print "Exception while processing a received transaction"
            print e
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
            print "Exception while checking if the node has to sign the next block"
            print e
            p2p.stop()
            sys.exit(0)

        #Process transactions from the user
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
                    #correct tx
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
            print "Exception while answering queries from OOR"
            print e 
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
            print "Exception while answering queries from the network"
            print e 
            p2p.stop()
            sys.exit(0)             

            
        #transaction pool
        try:
            if p2p.tx_pool_query():
                pool = chain.get_pending_transactions()
                p2p.answer_tx_pool_query(pool)
        except Exception as e:
            print "Exception while answering the transaction pool"
            print e  
            # Stop P2P
            p2p.stop()
            sys.exit(0)




if __name__ == "__main__":
    #run()

    keys, addresses = init_keystore()
    user = init_user()
    user.read_transactions()
    tx = user.get_tx()
    try:
        addresses.index(tx["from"])
    except:
        print "that key is not present in the keystore"
    try:
        addresses.index("hola")
    except:
        print "key hola is not present in the keystore"


    #chain = init_chain()
    #oor = init_oor()