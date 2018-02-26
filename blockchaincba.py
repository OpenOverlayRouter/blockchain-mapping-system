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
from own_exceptions import InvalidBlockSigner, UnsignedBlock

EXT_TX_PER_LOOP = 75
USER_TX_PER_LOOP = 1
#Number of times to add 100s to consensus calculation to identify signers in case of timeout
MAX_DISC_BLOCKS = 10

USE_ETH_NIST = 0
USE_ETH = 1
USE_NIST = 2
TIMEOUT = 240

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


def init_consensus(blockhash):
    return Consensus(blockhash, TIMEOUT)


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
    
    start_time = time.time()
    #seen_tx = []
    init_logger()

    mainLog.info("Initializing Chain")
    chain = init_chain()


    last_block = chain.get_head_block().header.number
    mainLog.debug("Last block: %s", last_block)
    mainLog.info("Initializing P2P")
    p2p = init_p2p(chain.get_head_block().header.number)

    mainLog.info("Initializing Consensus")
    consensus = init_consensus(USE_NIST)

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
    mainLog.info("Data sent to consensus: timestamp: %s -- block no. %s", timestamp, block_num)
    consensus.calculate_next_signer(myIPs, timestamp, block_num)


    while(not end):
        #Process new blocks
        try:
            block = p2p.get_block()
            while block is not None:
                mainLog.info("Received new block no. %s", block.number)
                res = False
                attempts = 0
                try: 
                    while attempts < MAX_DISC_BLOCKS and not res:
                        attempts = attempts + 1
                        signer = consensus.get_next_signer() 
                        mainLog.debug("Verifying new block signature, signer should be %s", signer)
                        mainLog.debug("Owner of the previous IP is address %s", chain.get_addr_from_ip(signer).encode("HEX"))
                        mainLog.debug("Coinbase in the block is: %s", block.header.coinbase.encode("HEX"))
                        try:                
                            res = chain.verify_block_signature(block, signer)
                        except InvalidBlockSigner:
                            res = False                        
                            mainLog.info("Invalid signer for this block, recalculating signer in case of timeout expiry")
                            timestamp = timestamp + TIMEOUT
                            consensus.calculate_next_signer(myIPs, timestamp, block_num)
                        except Exception as e:
                            raise e
                except UnsignedBlock as e:
                    mainLog.exception(e)
                    mainLog.error("Unsigned block. Skipping")
                    res = False
                except Exception as e:
                    mainLog.error("Block no. %s signautre is invalid!", block.number)
                    mainLog.exception(e)
                    raise e
                if res:
                    # correct block
                    chain.add_block(block)
                    myIPs = IPSet()
                    for i in range(len(keys)):
                        myIPs.update(chain.get_own_ips(keys[i].address))
                    mainLog.info("Updated own IPs: %s", myIPs)
                    timestamp = chain.get_head_block().header.timestamp
                    block_num = chain.get_head_block().header.number
                    mainLog.info("Data sent to consensus: timestamp: %s -- block no. %s", timestamp, block_num)
                    consensus.calculate_next_signer(myIPs, timestamp, block_num)
                else:
                    mainLog.error("Checked %s times for block signer but did not find it. Ignoring block...", attempts)
                    raise InvalidBlockSigner
                block = p2p.get_block()
        except Exception as e:
            mainLog.critical("Exception while processing a received block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        #Process transactions from the network
        processed = 0
        try:
            tx_ext = p2p.get_tx()
            while tx_ext is not None:
                #Check that the transaction has not been sent from this node or already processed
                processed = processed + 1
#                if tx_ext.hash not in seen_tx:
                if not (chain.in_chain(tx_ext) or chain.in_pool(tx_ext)):
                    mainLog.info("Received external transaction: to: %s hash %s", \
                    tx_ext.to.encode('HEX'), tx_ext.hash.encode('HEX'))
                    try:
#                        seen_tx.append(tx_ext.hash)                        
                        chain.add_pending_transaction(tx_ext)
                        # Correct tx
                        p2p.broadcast_tx(tx_ext)
                    except Exception as e:
                        mainLog.info("Discarded invalid external transaction: to: %s", \
                        tx_ext.to.encode("HEX"))
                        mainLog.exception(e)                        
                if processed < EXT_TX_PER_LOOP:
                    tx_ext = p2p.get_tx()
                else:
                    tx_ext = None
        except Exception as e:
            mainLog.critical("Exception while processing a received transaction")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)


        #Check if the node has to sign the next block
        try:
            block_num = chain.get_head_block().header.number
            me, signer = consensus.amISigner(myIPs, block_num)
            if me:
                mainLog.info("This node has to sign a block, selected IP: %s", signer)
                signing_addr = chain.get_addr_from_ip(signer)
                mainLog.info("Associated address: %s", signing_addr.encode("HEX"))
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
                mainLog.info("Sleeping 2s to give way to clock drift...")
                time.sleep(2)                                
                #Like receiving a new block
                chain.add_block(new_block)
                p2p.broadcast_block(new_block)
                myIPs = IPSet()
                for i in range(len(keys)):
                    myIPs.update(chain.get_own_ips(keys[i].address))            
                mainLog.info("Updated own IPs: %s", myIPs)
            timestamp = chain.get_head_block().header.timestamp
            block_num = chain.get_head_block().header.number
            #if curent time - timestamp >= TIMEOUT * 2 (means 1st backup signer KO, send a new timestamp to the conensus)
            if (time.time() - timestamp) > (2 * TIMEOUT):
                mainLog.warning("1st tiemout expired, selecting a new signer")
                timestamp = timestamp +  2 * TIMEOUT
            mainLog.info("Data sent to consensus: timestamp: %s -- block no. %s", timestamp, block_num)
            consensus.calculate_next_signer(myIPs, timestamp, block_num)
        except Exception as e:
            mainLog.critical("Exception while checking if the node has to sign the next block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        # Process transactions from the user
        processed = 0
        if (time.time() - start_time) > 1020:
            try:
                tx_int = user.get_tx()
                while tx_int is not None:
                    processed = processed + 1                    
                    try:
                        try:
                            key_pos = addresses.index(tx_int["from"])
                            #mainLog.debug("Found key in %s", key_pos)
                        except:
                            raise Exception("Key indicated in from field is not in present in the keystore")
                        key = keys[key_pos]
                        tx = chain.parse_transaction(tx_int)
                        tx.sign(key.privkey)
                        mainLog.info("Processing user transaction, from: %s --  to: %s -- hash %s -- value %s", \
                        tx_int["from"].encode("HEX"), tx_int["to"].encode("HEX"), tx.hash.encode("HEX"), tx_int["value"])
                        #mainLog.debug("TX signed. Info: v %s -- r %s -- s %s -- NONCE %s", tx.v, \
                        #tx.r, str(tx.s), tx.nonce)
                        # correct tx
                        try:
                            chain.add_pending_transaction(tx)
                        except Exception as e:
                            raise e
                        p2p.broadcast_tx(tx)
                        #mainLog.info("Sent transaction to the network, from: %s --  to: %s --  value: %s", \
                        #tx_int["from"].encode("HEX"), tx.to.encode("HEX"), tx.ip_network)
#                        seen_tx.append(tx.hash)
                    except Exception as e:
                        mainLog.error("Error when creating user transaction, ignoring transaction.")
                        mainLog.exception(e.message)
                    if processed < USER_TX_PER_LOOP:
                        tx_int = user.get_tx()
                    else:
                        tx_int = None
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



