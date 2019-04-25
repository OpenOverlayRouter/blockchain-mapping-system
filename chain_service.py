from block import Block, BlockHeader
from transactions import Transaction
from utils import null_address
import chain
from config import Env
import time
from genesis_helpers import mk_genesis_data
from db import _EphemDB
from apply import validate_transaction
import trie
import state
import rlp
from apply import apply_transaction
from utils import normalize_address, compress_random_no_to_int
from own_exceptions import UnsignedTransaction, DkgBlockRequiresGroupKey
#from state import State
from map_reply import Response, LocatorRecord, MapReplyRecord, MapServers
from netaddr import IPNetwork
import logging
import sys
import ConfigParser
import hashlib


databaseLog = logging.getLogger('Database')

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
DKG_RENEWAL_INTERVAL = config_data.getint('Consensus','dkg_renewal_interval')
DKG_NUMBER_PARTICIPANTS = config_data.getint('Consensus','dkg_participants')


class ChainService():
    """
    Manages the chain and requests to it.
    """

    def __init__(self, env=Env()):
        self.env = env
        self.db = self.env.db
        self.chain = chain.Chain(genesis=mk_genesis_data(self.env), env=self.env)
        self.transactions = []

    def add_pending_transaction(self, tx):
        assert isinstance(tx, Transaction)
        try:        
            validate_transaction(self.chain.state, tx)
        except Exception as e:
            raise e
            #databaseLog.info(e.message)
        # validate transaction
        try:
            # Transaction validation for broadcasting. Transaction is validated
            # against the current head candidate.
            if not tx.sender:  # sender is set and validated on Transaction initialization
                raise UnsignedTransaction(tx)
            else:
                if tx.sender == null_address:
                    raise UnsignedTransaction(tx)
        except Exception as e:
            raise e
            #databaseLog.info(e.message)
        self.transactions.append(tx)
        databaseLog.info("From: chain_service: Added transaction %s to the pool, from: %s --  to: %s", \
        tx.hash.encode("HEX"), tx.sender.encode("HEX"), tx.to.encode("HEX"))
        

    # creates a block with the list of pending transactions, creates its tries and returns it
    def create_block(self, coinbase, random_no, group_key, count):
        
        self.chain.process_time_queue()
        prevhash = self.chain.head_hash
        prevnumber = self.chain.state.block_number
        coinbase = normalize_address(coinbase)
        if (prevnumber + 1) % DKG_RENEWAL_INTERVAL == 0: 
            if ((group_key is None) or (group_key == '')):
	            raise DkgBlockRequiresGroupKey()
        else:
            group_key = ''
        block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, \
            number=prevnumber + 1, coinbase=coinbase, random_number=random_no,  group_pubkey=group_key, count=count))
        snapshot = self.chain.state.to_snapshot()
        s = state.State().from_snapshot(snapshot, Env(_EphemDB()))
        databaseLog.info("Creating block with block number %s", str(prevnumber+1))
        for tx in self.transactions:
            if sys.getsizeof(block) < 1048576:
                try:
                    dictionary = {}
                    if (prevnumber+1) % 2 == 0 and int(tx.afi) == 1:  # the next block has to be an IPv4 one
                        apply_transaction(s, tx, dictionary)
                        block.transactions.append(tx)
                    elif (prevnumber+1) % 2 != 0 and int(tx.afi) == 2:  # the next block has to be an IPv6 one
                        apply_transaction(s, tx, dictionary)
                        block.transactions.append(tx)
                except Exception as e:
                    databaseLog.info(e.message)
            else:
                databaseLog.info("Block number %s filled to max. size", str(prevnumber+1))

        self._create_tries(block)
        return block

    def validate_transaction(self, tx):
        return self.chain.validate_transaction(tx)

    def validate_block(self):
        self.chain.process_time_queue()
        return self.chain.validate_block()

    def verify_block_signature(self,block,ip):
        return self.chain.verify_block_signature(block,ip)

    # creates the tx_trie and state trie of a block
    def _create_tries(self, block):
        t = trie.Trie(_EphemDB())
        snapshot = self.chain.state.to_snapshot()

        temp_state = self.chain.state.clone()

        dictionary = {}
        for index, tx in enumerate(block.transactions):
            t.update(rlp.encode(index), rlp.encode(tx))
            apply_transaction(temp_state, tx, dictionary)
        block.header.tx_root = t.root_hash
        block.header.state_root = temp_state.trie.root_hash

    # adds the block to the chain and eliminates from the pending transactions those transactions present in the block
    def add_block(self, block):
        assert isinstance(block, Block)
        blocknumber = block.header.number
        if blocknumber % 2 == 0:  # received block has to be IPv4
            for tx in block.transactions:
                if tx.afi != 1:
                    raise Exception("IPv6 block with an IPv4 transaction, afi detected: %s", str(tx.afi))
        elif blocknumber % 2 != 0: # received block has to be IPv6
            for tx in block.transactions:
                if tx.afi != 2:
                    raise Exception("IPv4 block with an IPv6 transaction, afi detected: " + str(tx.afi))
        self.chain.add_block(block)
        databaseLog.debug("TX management: deleting transactions added to the chain from the pool")
        for tx in block.transactions:
            if tx in self.transactions:
                self.transactions.remove(tx)
        invalid_tx = []
        databaseLog.debug("TX management: purging tx pool")
        for tx in self.transactions:
            try:
                validate_transaction(self.chain.state,tx)
            except Exception:
                invalid_tx.append(tx)
        if invalid_tx:
            for tx in invalid_tx:
                databaseLog.debug("Deleted invalid transaction %s", tx.hash.encode('HEX'))
                self.transactions.remove(tx)
        databaseLog.debug("TX management: pool size after purging: %s", len(self.transactions))


    # returns the transaction whose hash is 'tx'
    def get_transaction(self, tx):
        return self.chain.get_transaction(tx)

    # returns the list of pending transactions (not yet included in a block)
    def get_pending_transactions(self):
        return self.transactions

    def get_head_block(self):
        return self.chain.get_head_block()

    # returns the block whose hash is 'block'
    def get_block(self, block):
        return self.chain.get_block(block)

    # returns the block whose number is 'block'
    def get_block_by_number(self, block):
        return self.chain.get_block_by_number(block)

    # returns the own ips of the address
    def get_own_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).own_ips

    # returns the delegated ips of the address
    def get_delegated_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).delegated_ips

    # returns the received ips of the address
    def get_received_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).received_ips

    # returns the map_server of the address
    def get_map_server(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).map_server

    # returns the locator of the address
    def get_locator(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).locator

    # returns the state of the chain
    def get_state(self):
        return self.chain.state

    # creates a transaction with de data in the transaction_data dictionary
    def parse_transaction(self, transaction_data):
        return Transaction(self.chain.state.get_nonce(transaction_data["from"]), transaction_data["category"],
                           transaction_data["to"], transaction_data["afi"], transaction_data["value"],
                           transaction_data.get("metadata"), int(time.time()))

    # queries the eid to the blockchain and returns the response
    def query_eid(self, ipaddr, nonce):
        try:
            address = normalize_address(self.chain.patricia.get_value(str(IPNetwork(ipaddr).ip)))
            balance = self.chain.state.get_balance(address)
            if balance is not None:
                if len(balance.map_server.keys()) > 0:
                    map_servers = MapServers(info=balance.map_server.keys())
                    resp = Response(nonce=nonce, info=map_servers)
                    return resp.to_bytes()
                elif len(balance.locator.keys()) > 0:
                    locator_records = []
                    for key in balance.locator.keys():
                        locator_records.append(LocatorRecord(priority=balance.locator[key][0],
                                                             weight=balance.locator[key][1],
                                                             locator=key))
                    map_reply = MapReplyRecord(eid_prefix=IPNetwork(ipaddr), locator_records=locator_records)
                    resp = Response(nonce=nonce, info=map_reply)
                    return resp.to_bytes()
            else:
                databaseLog.info("Address %s has no balance", str(address))
                print("Address %s has no balance", str(address))
        except:
            print("IP address %s is not owned by anybody", str(ipaddr))
            databaseLog.info("IP address %s is not owned by anybody", str(ipaddr))
        
        return None

    def in_chain(self,tx):
        assert isinstance(tx, Transaction)
        return self.db._has_key(b'txindex:' + tx.hash)

    def in_pool(self,tx):
        assert isinstance(tx, Transaction)
        return tx in self.transactions

    #returns the corresponing blockchain address for the specified IP address    
    def get_addr_from_ip(self, ipaddr):
        return normalize_address(self.chain.patricia.get_value(str(ipaddr)))
        
    #Retruns the group key from the last DKG
    def get_current_group_key(self):
        last_block_no = self.get_head_block().header.number
        last_old_dkg_block = last_block_no - (last_block_no % DKG_RENEWAL_INTERVAL)
        return self.get_block_by_number(last_old_dkg_block).header.group_pubkey
        
    #Selects a group of addresses to perform the DKG
    def get_current_dkg_group(self):
        #Recover random no. from block previous trigger new DKG
        last_block_no = self.get_head_block().header.number
        last_old_dkg_block = last_block_no - (last_block_no % DKG_RENEWAL_INTERVAL)
        random_no = compress_random_no_to_int(self.get_block_by_number(last_old_dkg_block).header.random_number)
        
        #List all addresses at the moment in the chain
        all_addresses = self.chain.get_all_current_addresses()
        databaseLog.debug("Recovered the list of current addresses, lenght: %s", len(all_addresses))
        databaseLog.debug("Addresses in the list:")
        for addr in all_addresses:    
            databaseLog.debug(addr.encode('hex'))
        #Randomly select participants from all the addresses
        dkg_group = []
        for i in range(DKG_NUMBER_PARTICIPANTS):
            random_pos = random_no % len(all_addresses)
            dkg_group.append(all_addresses.pop(random_pos))            
            random_no = compress_random_no_to_int(hashlib.sha256(str(random_no)).hexdigest(), 16)      
        return dkg_group
    
    def extract_first_ip_from_address(self, address):
        ipset = self.get_delegated_ips(address)[address]
        for ip in ipset:
            return ip
        
        
        
