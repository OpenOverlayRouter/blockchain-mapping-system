# -*- coding: utf-8 -*-

import sys
import ConfigParser
import time, os, glob, errno, hashlib
from netaddr import IPSet

from config import Env
from db import LevelDB
from chain_service import ChainService
from keystore import Keystore
import consensus as cons
from p2p import P2P
import logging
import logging.config
import logger
from user import Parser
from utils import normalize_address, compress_random_no_to_int
from oor import Oor
from share_cache import Share_Cache
from own_exceptions import InvalidBlockSigner, UnsignedBlock, BlsInvalidGroupSignature


mainLog = logging.getLogger('Main')

def open_log_block_process_delay():
    try:    
        out = open('delays-process-block.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
    return out

def open_log_delay_create_txs():
    try:    
        out = open('delays-create-txs.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
    return out


def init_chain():
    db = LevelDB("./chain")
    env = Env(db)
    return ChainService(env)


def init_p2p(last_block_num):
    # P2P initialization
    p2p = P2P(last_block_num)
    while (p2p.bootstrap()):
        time.sleep(1)
    mainLog.info("P2P Bootstrap finished")
    return p2p


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

    #Load config    
    config_data = ConfigParser.RawConfigParser()
    config_data.read('chain_config.cfg')   
    EXT_TX_PER_LOOP = config_data.getint('Transaction generation and processing','ext_tx_per_loop')
    USER_TX_PER_LOOP = config_data.getint('Transaction generation and processing','user_tx_per_loop')
    START_TIME = config_data.getint('Transaction generation and processing','start_time')
    DKG_RENEWAL_INTERVAL = config_data.getint('Consensus','dkg_renewal_interval')
    BLOCK_TIME = config_data.getint('General','block_time')
    TIMEOUT = config_data.getint('General','timeout')
    DKG_TIMEOUT = config_data.getint('Consensus','dkg_timeout')

    #Telemetry initialization
    start_time = time.time()
    
    init_logger()

    delays_blocks = open_log_block_process_delay()
    delays_txs = open_log_delay_create_txs()

    #Modules initialization
    mainLog.info("Initializing Chain")
    chain = init_chain()

    last_block = chain.get_head_block().header.number
    mainLog.debug("Last block: %s", last_block)
    mainLog.info("Initializing P2P")
    p2p = init_p2p(chain.get_head_block().header.number)
    
    

    mainLog.info("Initializing Keystore")
    keys, addresses = init_keystore()
    mainLog.info("Loaded %s keys", len(keys))
    mainLog.info("----------------LOADED ADDRESSES---------------------")
    mainLog.info([add.encode("HEX") for add in addresses])
    mainLog.info("----------------END ADDRESS LIST---------------------")
    
    mainLog.info("Initializing Parser")
    user = init_user()
    try:
        user.read_transactions("./transactions.txt")
    except Exception as e:
        mainLog.critical("Exception while reading user transactions")
        mainLog.exception(e)
        p2p.stop()
        sys.exit(0)
        

    mainLog.info("Initializing OOR")
    oor = init_oor()

    #Variables initialization
    end = 0
    count = 0
    dkg_on = False
    exit_from_dkg = False
    processed_user = 0
    user_tx_count = 0
    
    block_num = chain.get_head_block().header.number
    timestamp = chain.get_head_block().header.timestamp    
    current_random_no = chain.get_head_block().header.random_number.encode('hex')
    current_group_sig = chain.get_head_block().header.group_sig
    current_group_key = chain.get_current_group_key()
    
    my_dkgIDs = []
    
    myIPs = IPSet()
    for i in range(len(keys)):
        myIPs.update(chain.get_own_ips(keys[i].address))
    mainLog.info("Own IPs at startup are: %s", myIPs)
    
    dkg_group = chain.get_current_dkg_group()
    in_dkg_group, my_dkgIDs = find_me_in_dkg_group(dkg_group, addresses)     
    
    mainLog.info("Initializing Consensus")
    consensus = cons.Consensus(dkg_group, my_dkgIDs, current_random_no, current_group_key, block_num, current_group_sig)

    isMaster = load_master_private_keys(consensus, block_num)
    if not in_dkg_group:
        consensus.store_ids(dkg_group)
    else:
        mainLog.warning("TODO: nodes that belong to the DKG group and connect after the DKG do not have private keys, so they shouldn't create shares. Needs to be disabled!")
        if not isMaster:
	    not_create_shares = True 
    cache = Share_Cache()
    
        
    before = time.time()
    current_random_no, block_num, count = perform_bootstrap(chain, p2p, consensus, delays_blocks, delays_txs, DKG_RENEWAL_INTERVAL ,current_random_no, block_num, count)
    after = time.time()
    elapsed = after - before
    mainLog.info("Bootstrap finished. Elapsed time: %s", elapsed)
    timestamp = chain.get_head_block().header.timestamp
    current_group_sig = chain.get_head_block().header.group_sig
    current_group_key = chain.get_current_group_key()
    
    while(not end):
        
        #Process new blocks. DOES NOT support bootstrap
        try:
            block = p2p.get_block()
            while block is not None or dkg_on:
                # Only nodes that do NOT belong to the DKG get stuck here until they receive the block with the new group key
                mainLog.info("Received new block no. %s", block.number)
                
                res = False
                try: 
                    signer = consensus.get_next_signer(block.count) 
                    if in_dkg_group and exit_from_dkg:
                        # We ONLY enter here if the node belongs to the DGK group and just finished a new DKG
                        exit_from_dkg = False
                        if block.header.group_pubkey != consensus.get_current_group_key():
                            mainLog.error("FATAL ERROR. A node in the DKG group received a block with a Group Public Key not matching the generated from the DKG.")
                            raise e
                        signer = chain.extract_first_ip_from_address(signing_addr)
                    elif dkg_on:
                        # We ONLY enter here if the nodes DOES NOT belong to the DKG group and is waiting for a current DKG to finish
                        signer = chain.extract_first_ip_from_address(signing_addr)
                        consensus.set_current_group_key(block.header.group_pubkey)
                        dkg_on = False
                    mainLog.debug("Verifying new block signature, signer should be %s", signer)
                    mainLog.debug("Owner of the previous IP is address %s", chain.get_addr_from_ip(signer).encode("HEX"))
                    mainLog.debug("Coinbase in the block is: %s", block.header.coinbase.encode("HEX"))
                    res = chain.verify_block_signature(block, signer)
                except UnsignedBlock as e:
                    mainLog.exception(e)
                    mainLog.error("Unsigned block. Skipping")
                    res = False
                except InvalidBlockSigner as e:
                    mainLog.exception(e)
                    mainLog.error("Block no. %s signautre is invalid! Ignoring.", block.number)
                    res = False                        
                except Exception as e:
                    mainLog.error("Unrecoverable error when checking block signature. Exiting.", block.number)
                    mainLog.exception(e)
                    raise e
                if res:
                    # correct block
                    before = time.time()
                    chain.add_block(block)
                    after = time.time()
                    delay = after - before
                    delays_blocks.write(str(block.number) + ',' + str(delay) + '\n' )
                    delays_txs.write("Added new block no." + str(block.number) + '\n')
                    timestamp = chain.get_head_block().header.timestamp
                    block_num = chain.get_head_block().header.number                                        
                    #after a correct block: reset BLS and create and broadcast new shares (like receiving a new block)
                    consensus.reset_bls()
                    if in_dkg_group:
                        count = 0
                        new_shares = consensus.create_shares(block_num, count)
                        for share in new_shares:
                            p2p.broadcast_share(share)
                            cache.store_bls(share)
                            mainLog.info("Sent a new share to the network")
                else:
                    mainLog.error("Received an erroneous block. Ignoring block...")
                    
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
                if not (chain.in_chain(tx_ext) or chain.in_pool(tx_ext)):
                    mainLog.info("Received external transaction: to: %s hash %s", \
                    tx_ext.to.encode('HEX'), tx_ext.hash.encode('HEX'))
                    try:
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


        #Check if the node has to sign the next block. Control also timeouts
        #Before we wait for the block time
        try:
            timestamp = chain.get_head_block().header.timestamp
            block_num = chain.get_head_block().header.number
            if ((time.time()-timestamp) >= BLOCK_TIME):
                #Time to create a new block
                if (time.time() - timestamp) >= TIMEOUT:
                #The expected signer didn't create a block. Trigger a recalculation of the random number to select a new signer
                #TODO: does NOT work because it will enter all the time when the timeout expires
#                    count = count + 1
#                    timeout_expired =  True
#                    if count == 0:
#                        consensus.reset_bls()
#                    consensus.create_share(count)
#                    p2p.broadcast_share(new_share)
#                    mainLog.info("Timeout expired. Recalculated random no and sent a new share to the network")
                    mainLog.info("Contextual information: Current time: %s --Last block timestamp: %s --Last random number: %s --Last block number: %s", \
                                 time.time(), timestamp, consensus.get_current_random_no(), block_num)
                    raise Exception("FATAL ERROR, Block tiemout expired. The feature to re-calculte the random number after a block timeout exprity is not implemented. Stopping...")
                if consensus.shares_ready() or exit_from_dkg:
                    if not exit_from_dkg:
                        #Normal operation
                        signer = consensus.get_next_signer(count) 
                        signing_addr = chain.get_addr_from_ip(signer)
                    else:
                        #When we exit a new DKG round, the variable signing_addr stores the next signer (we are temporarily overriding the BLS RN generation)
                        exit_from_dkg = False
                    if signing_addr in addresses:
                        mainLog.info("This node has to sign a block, selected IP: %s", signer)
                        mainLog.info("Associated address: %s", signing_addr.encode("HEX"))
                        new_block = chain.create_block(signing_addr, consensus.get_current_random_no(), \
                                    consensus.get_current_group_key(), consensus.get_current_group_sig(), count)
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
                        before = time.time()
                        chain.add_block(new_block)
                        after = time.time()
                        delay = after - before
                        delays_blocks.write(str(new_block.number) + ',' + str(delay) + '\n' )                
                        delays_txs.write("Added new block no." + str(new_block.number) + '\n')
                        p2p.broadcast_block(new_block)
                        #after a correct block, create and broadcast new share    
                        count = 0
                        #timeout_expired = False
                        consensus.reset_bls()
                        if in_dkg_group:
                            count = 0
                            new_shares = consensus.create_shares(new_block.number, count)
                            for share in new_shares:
                                p2p.broadcast_share(share)
                                cache.store_bls(share)
                                mainLog.info("Sent a new share to the network")                        

        except Exception as e:
            mainLog.critical("Exception while checking if the node has to sign the next block")
            mainLog.exception(e)
            p2p.stop()
            sys.exit(0)

        # Process transactions from the user
        if ((time.time() - start_time) > START_TIME or isMaster) and not dkg_on:
            if user_tx_count == 3:            
                try:
                    tx_int = user.get_tx()
                    while tx_int is not None:
                        before = time.time()
                        processed_user = processed_user + 1                    
                        user_tx_count = 0
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
                            after = time.time()
                            delay = after - before
                            delays_txs.write(str(tx.hash.encode("HEX")) + ',' + str(delay) + '\n' )
                            #mainLog.info("Sent transaction to the network, from: %s --  to: %s --  value: %s", \
                            #tx_int["from"].encode("HEX"), tx.to.encode("HEX"), tx.ip_network)
    #                        seen_tx.append(tx.hash)
                        except Exception as e:
                            mainLog.error("Error when creating user transaction, ignoring transaction.")
                            mainLog.exception(e.message)
#                        Temporarily diabled because we want 1 tx per 2 loops
#                        if processed < USER_TX_PER_LOOP:
#                            tx_int = user.get_tx()
#                        else:
#                            tx_int = None
                        tx_int = None
                except Exception as e:
                    mainLog.exception(e)
                    p2p.stop()
                    sys.exit(0)
            else:
                user_tx_count = user_tx_count + 1

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

#########Answer queries from the network
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
    
########Consensus        
        #Get shares from the network
        try:
            share = p2p.get_share()
            while share is not None:
                if not cache.in_bls_cache(share):
                    msg = str(current_random_no) + str(block_num) + str(count)
                    res = consensus.store_share(share, msg, block_num)
                    if res:
                        current_random_no = consensus.get_current_random_no()
                    cache.store_bls(share)
                    p2p.broadcast_share(share)
                share = p2p.get_share()
        except Exception as e:
            mainLog.critical("Exception while processing received shares")
            mainLog.exception(e)
            # Stop P2P
            p2p.stop()
            sys.exit(0)
 
        #DKG management
       
        #Trigger new DKG               
        try:
            if ((block_num + 1) % DKG_RENEWAL_INTERVAL == 0) and not dkg_on:
                dkg_on = True
                dkg_group = chain.get_current_dkg_group()
                in_dkg_group, my_dkgIDs = find_me_in_dkg_group(dkg_group, addresses)     
                if in_dkg_group:        
                    to_send = consensus.new_dkg(dkg_group, my_dkgIDs)
                    for dkg_share in to_send:
                        cache.store_dkg(dkg_share.secret_key_share_contrib.encode("HEX"))
                        p2p.send_dkg_share(dkg_share)
                else:
                    # Configure nodes that do not participate in the DKG so they can verfiy BLS shares later
                    consensus.store_ids(dkg_group)                    
                #Define new signer that has to be in the dkg_group. Selected randomly from the people in the group (temporal override of the BLS RN generation)
                random_no = chain.get_block_by_number(block_num).header.random_number
                random_pos = compress_random_no_to_int(random_no, 16) % len(dkg_group)
                # signing_addr will be used in block RX and block creation code in the beginning of the loop
                signing_addr = dkg_group[random_pos]
        except Exception as e:
            mainLog.critical("Exception while creating DKG shares")
            mainLog.exception(e)
            # Stop P2P
            p2p.stop()
            sys.exit(0)
        
        #Collect DKG shares for the new DKG                
        try:        
            #During DKG, the prototype only works on DKG
            if in_dkg_group:            
                while dkg_on:
                #WE STAY HERE FOR THE WHOLE DKG
                    dkg_share = p2p.get_dkg_share() 
                    while dkg_share is not None:
                        mainLog.info("Received new DKG share")
                        if dkg_share.to.encode('hex') in my_dkgIDs and not cache.in_dkg_cache(dkg_share.secret_share_contrib.encode("HEX")):
                            consensus.verify_dkg_contribution(dkg_share)
                            cache.store_dkg(dkg_share.secret_share_contrib.encode("HEX"))
                            if consensus.allSharesReceived():
                                dkg_on = False
                                exit_from_dkg = True
                            elif (time.time() - timestamp) >= DKG_TIMEOUT:
                                mainLog.critical("Fatal Error. DKG renewal timeout expired. Stopping...")
                                raise e
                        else:
                            p2p.send_dkg_share(dkg_share)
                        dkg_share = p2p.get_dkg_share() 
            elif dkg_on:
                mainLog.info("This node is not participating in the DKG. Will sleep for 3 min and wait for a block with the new public key")
                time.sleep(180) 
                if (time.time() - timestamp) >= DKG_TIMEOUT:
                    mainLog.critical("Fatal Error. DKG renewal timeout expired. Stopping...")
                    raise e
        except Exception as e:
            mainLog.critical("Exception while processing received DKG shares")
            mainLog.exception(e)
            # Stop P2P
            p2p.stop()
            sys.exit(0)
                
def perform_bootstrap(chain, p2p, consensus, delays_blocks, delays_txs, DKG_RENEWAL_INTERVAL, last_random_no, last_block_num, count):
    #Code here is exaclty equal to the 'Process new blocks' part in the main, but without generating shares after adding the block.
    #And during initialization, consenus is ready to calculte new signers (random number is stored)
    try:
        block = p2p.get_block()
        while block is not None:
            mainLog.info("[BOOTSTRAP]: Received new block no. %s", block.number)
            
            res = False
            try: 
                if (block.number % DKG_RENEWAL_INTERVAL == 0):
                    # Next signer changes when new DKG, replicate what we do when we trigger a new DKG and we are not in the DKG group
                    dkg_group = chain.get_current_dkg_group()
                    random_pos = compress_random_no_to_int(last_random_no, 16) % len(dkg_group)
                    signing_addr = dkg_group[random_pos]
                    signer = chain.extract_first_ip_from_address(signing_addr)
                    consensus.set_current_group_key(block.header.group_pubkey)
                #Verify group sig of the block to authenticate random number                
                expected_message = str(last_random_no) + str(last_block_num) + str(count)
                
                if consensus.bootstrap_verify_group_sig(expected_message, block.header.group_sig):
                    mainLog.debug("[BOOTSTRAP]: previous random no: %s", last_random_no)    
                    mainLog.debug("[BOOTSTRAP]: hash of group signature: %s", hashlib.sha256(block.header.group_sig).hexdigest())
                    if block.header.random_number.encode('hex') == hashlib.sha256(block.header.group_sig).hexdigest():
                        #Manually force the random number because we cannot calculat it during bootstrap (BLS already done)                                        
                        last_random_no = block.header.random_number.encode('hex')                        
                        consensus.bootstrap_only_set_random_no_manual(last_random_no)
                        consensus.bootstrap_only_set_group_sig_manual(block.header.group_sig)
                        signer = consensus.calculate_next_signer(last_block_num)
                        mainLog.debug("[BOOTSTRAP]: Verify Group Signature OK")
                        mainLog.debug("[BOOTSTRAP]: New random number is :%s", last_random_no)
                    else:                    
                        mainLog.critical("[BOOTSTRAP]: FATAL: random number in block does not match group signature hash")
                        raise Exception
                else: 
                    raise BlsInvalidGroupSignature()                 
                mainLog.debug("[BOOTSTRAP]: Verifying new block signature, signer should be %s", signer)
                mainLog.debug("[BOOTSTRAP]: Owner of the previous IP is address %s", chain.get_addr_from_ip(signer).encode("HEX"))
                mainLog.debug("[BOOTSTRAP]: Coinbase in the block is: %s", block.header.coinbase.encode("HEX"))
                res = chain.verify_block_signature(block, signer)
            except UnsignedBlock as e:
                mainLog.exception(e)
                mainLog.error("[BOOTSTRAP]: Unsigned block. Skipping")
                res = False
            except InvalidBlockSigner as e:
                mainLog.exception(e)
                mainLog.error("[BOOTSTRAP]: Block no. %s signautre is invalid! Ignoring.", block.number)
                res = False                        
            except Exception as e:
                mainLog.error("[BOOTSTRAP]: Unrecoverable error when checking block signature. Exiting.", block.number)
                mainLog.exception(e)
                raise e
            if res:
                # correct block
                before = time.time()
                chain.add_block(block)
                after = time.time()
                delay = after - before
                delays_blocks.write(str(block.number) + ',' + str(delay) + '\n' )
                delays_txs.write("Added new block no." + str(block.number) + '\n')                
                last_block_num = block.number
            else:
                mainLog.error("[BOOTSTRAP]: Received an erroneous block. Ignoring block...")
            block = p2p.get_block()
    except Exception as e:
        mainLog.critical("Exception in bootstrap process (block verification)")
        mainLog.exception(e)
        p2p.stop()
        sys.exit(0)

    return last_random_no, last_block_num, count

def find_me_in_dkg_group(current_group, node_addresses):
    
    in_dkg_group = False
    my_dkg_ids = []
    for address in node_addresses:
        if address in current_group:
            in_dkg_group = True
            my_dkg_ids.append(address)
    if in_dkg_group:
        mainLog.debug("Group selection process. This node is in the DKG group, with the following blockchain addresses: %s", [addr.encode('hex') for addr in my_dkg_ids])
    else:
        mainLog.debug("Group selection process. This node is NOT in the DKG group.")
    return in_dkg_group, my_dkg_ids

def load_master_private_keys(consensus, block_num):
    try:    
        priv_keys = open('master-private-dkg-keys.txt', 'r')
    except IOError as e:
        if e.errno == errno.ENOENT:            
            #File does not exist, means it is not the master node
            return False
        else:
            raise e
    except Exception as e: 
        print e
        sys.exit(1)
    
    mainLog.info("Detected master private key file. Perfoming manual setup of DKG private keys and initial BLS.")
    sec_keys = {}
    for line in priv_keys:
        content = line.split(' ')
        sec_keys[normalize_address(content[0])] = content[1].rstrip('\n')        
    priv_keys.close()
    consensus.bootstrap_master_add_secret_keys_manual(sec_keys)
    consensus.create_shares(block_num)
    return True
        

if __name__ == "__main__":
    run()
