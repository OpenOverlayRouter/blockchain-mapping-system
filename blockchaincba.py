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
#from netaddr import IPNetwork
#from ipaddr import IPv4Network
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
import time


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
        #print ("key %s loaded from %s", key, file)
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
    bootstrap = True    
    start_time = time.time()
    seen_tx = []
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
    mainLog.info("----------------LOADED ADDRESSES---------------------")
    for add in addresses:
        mainLog.info(add.encode("HEX"))
    mainLog.info("----------------END ADDRESS LIST---------------------")
    
    mainLog.info("Initializing Parser")
    user = init_user()
    try:
        user.read_transactions()
    except Exception as e:
        mainLog.critical("Exception while reading user transactions")
        mainLog.exception(e)
        p2p.stop()
        sys.exit(0)
        

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
                mainLog.debug("Verifying new block signature, signer should be %s", signer)
                mainLog.debug("Owner of the previous IP is address %s", chain.get_addr_from_ip(signer).encode("HEX"))
                mainLog.debug("Coinbase in the block is: %s", block.header.coinbase.encode("HEX"))
                res = chain.verify_block_signature(block, signer)
                if res:
                    # correct block
                    chain.add_block(block)
                    myIPs = IPSet()
                    for i in range(len(keys)):
                        myIPs.update(chain.get_own_ips(keys[i].address))
                    mainLog.info("Updated own IPs: %s", myIPs)
                    timestamp = chain.get_head_block().header.timestamp
                    block_num = chain.get_head_block().header.number
                    consensus.calculate_next_signer(myIPs, timestamp, block_num)
                else:
                    mainLog.error("Block no. %s signautre is invalid!", block.number)
                block = p2p.get_block()
        except Exception as e:
            mainLog.critical("Exception while processing a received block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        #Process transactions from the network
        try:
            tx_ext = p2p.get_tx()
            if tx_ext is not None:
            #while tx_ext is not None:
                #Check that the transaction has not been sent from this node or already processed
                if tx_ext.hash not in seen_tx:
                    mainLog.info("Received external transaction: to: %s", \
                    tx_ext.to.encode('HEX'))
                    try:
                        chain.add_pending_transaction(tx_ext)
                        # Correct tx
                        p2p.broadcast_tx(tx_ext)
                        seen_tx.append(tx_ext.hash)
                    except:
                        mainLog.info("Discarded invalid external transaction: to: %s", \
                        tx_ext.to.encode("HEX"))
                        pass                      
#                #rate limit transaction processing after bootsrap
#                if bootstrap:
#                    #get new transactions to process
#                    tx_ext = p2p.get_tx()
#                    if (time.time() - start_time) > 30:
#                        bootstrap = False
#                        mainLog.info("Finished 50s tx bootstrap.")
#                else:
#                    tx_ext = None                
        except Exception as e:
            mainLog.critical("Exception while processing a received transaction")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)


        #Check if the node has to sign the next block
        try:
            me, signer = consensus.amISigner(myIPs, block_num)
            if me:
                mainLog.info("This node has to sign a block, selected IP: %s", signer)
                signing_addr = chain.get_addr_from_ip(signer)
                mainLog.info("Associated address: %s", signing_addr.encode("HEX"))                
                #new_block = chain.create_block(keys[0].address)
                mainLog.info("Sleeping 14s to give way to clock drift...")
                time.sleep(14)                
                new_block = chain.create_block(signing_addr)
                try:
                    key_pos = addresses.index(signing_addr)
                except:
                    raise Exception("FATAL ERROR: This node does not own the indicated key to sign the block (not present in the keystore)")
                sig_key = keys[key_pos]
                new_block.sign(sig_key.privkey)
                mainLog.info("Created new block no. %s, timestamp %s, coinbase %s", \
                    new_block.header.number, new_block.header.timestamp, new_block.header.coinbase.encode("HEX"))
                mainLog.info("New block signature data: v %s -- r %s -- s %s", new_block.v, new_block.r, new_block.s)
                mainLog.info("This block contains %s transactions", new_block.transaction_count)
                #Like receiving a new block
                chain.add_block(new_block)
                #Revisar
                p2p.broadcast_block(new_block)
                myIPs = IPSet()
                for i in range(len(keys)):
                    myIPs.update(chain.get_own_ips(keys[i].address))            
                mainLog.info("Updated own IPs: %s", myIPs)
                timestamp = chain.get_head_block().header.timestamp
                block_num = chain.get_head_block().header.number
                consensus.calculate_next_signer(myIPs, timestamp, block_num)
        except Exception as e:
            mainLog.critical("Exception while checking if the node has to sign the next block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        # Process transactions from the user
        if (time.time() - start_time) > 600:
            try:
                tx_int = user.get_tx()
                if tx_int is not None:
                    mainLog.info("Processing user transaction, from: %s --  to: %s", tx_int["from"].encode("HEX"), tx_int["to"].encode("HEX"))
                    try:
                        try:
                            key_pos = addresses.index(tx_int["from"])
                            #mainLog.debug("Found key in %s", key_pos)
                        except:
                            raise Exception("Key indicated in from field is not in present in the keystore")
                        key = keys[key_pos]
                        tx = chain.parse_transaction(tx_int)
                        tx.sign(key.privkey)
                        #mainLog.debug("TX signed. Info: v %s -- r %s -- s %s -- NONCE %s", tx.v, \
                        #tx.r, str(tx.s), tx.nonce)
                        # correct tx
                        try:
                            chain.add_pending_transaction(tx)
                        except Exception as e:
                            raise Exception(e)
                        p2p.broadcast_tx(tx)
                        #mainLog.info("Sent transaction to the network, from: %s --  to: %s --  value: %s", \
                        #tx_int["from"].encode("HEX"), tx.to.encode("HEX"), tx.ip_network)
                        seen_tx.append(tx.hash)
                    except Exception as e:
                        mainLog.error("Error when creating user transaction")
                        mainLog.exception(e.message)
                        raise Exception(e)
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
                for number in block_numbers:
                    response.append(chain.get_block_by_number(number))
                p2p.answer_block_queries(response)
        except Exception as e:
            mainLog.critical("Exception while answering queries from the network")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)


        #transaction pool
        try:
            if p2p.tx_pool_query():
                mainLog.info("Answering tx pool query")
                pool = chain.get_pending_transactions()
                p2p.answer_tx_pool_query(pool)
        except Exception as e:
            mainLog.critical("Exception while answering the transaction pool")
            mainLog.exception(e)
            # Stop P2P
            p2p.stop()
            sys.exit(0)

if __name__ == "__main__":
    run()



