import json
import time
import itertools
import trie
from utils import big_endian_to_int
import rlp
from rlp.utils import encode_hex
from config import Env
from state import State, dict_to_prev_header
from block import Block, BlockHeader, FakeHeader
from genesis_helpers import state_from_genesis_declaration, mk_basic_state, initialize, initialize_genesis_keys
from db import EphemDB

config_string = ':info'  # ,eth.chain:debug'


# Update block variables into the state
def update_block_env_variables(state, block):
    state.timestamp = block.header.timestamp
    state.gas_limit = block.header.gas_limit
    state.block_number = block.header.number
    state.block_coinbase = block.header.coinbase
    state.block_difficulty = block.header.difficulty


def validate_header(state, header):
    parent = state.prev_headers[0]
    if parent:
        if header.prevhash != parent.hash:
            raise ValueError("Block's prevhash and parent's hash do not match: block prevhash %s parent hash %s" %
                             (encode_hex(header.prevhash), encode_hex(parent.hash)))
        print("HEADER NUMBER " + str(header.number))
        print("PARENT NUMBER " + str(parent.number))
        if header.number != parent.number + 1:
            raise ValueError(
                "Block's number is not the successor of its parent number")
        if header.timestamp <= parent.timestamp:
            raise ValueError("Timestamp equal to or before parent")
        if header.timestamp >= 2**256:
            raise ValueError("Timestamp waaaaaaaaaaayy too large")
    return True


# Make the root of a receipt tree
def mk_transaction_sha(receipts):
    t = trie.Trie(EphemDB())
    for i, receipt in enumerate(receipts):
        print(receipt)
        t.update(rlp.encode(i), rlp.encode(receipt))
    return t.root_hash


# Validate that the transaction list root is correct
def validate_transaction_tree(state, block, db):
    if block.header.tx_root != mk_transaction_sha(block.transactions):
        print(trie.BLANK_ROOT.encode("HEX"))
        print(str(block.header.tx_root).encode("HEX"))
        print(mk_transaction_sha(block.transactions).encode("HEX"))
        raise ValueError("Transaction root mismatch: header %s computed %s, %d transactions" %
                         (encode_hex(str(block.header.tx_root)), encode_hex(str(mk_transaction_sha(block.transactions))),
                          len(block.transactions)))
    return True


# Applies the block-level state transition function
def apply_block(state, block, db):
    # Pre-processing and verification
    snapshot = state.snapshot()
    try:
        # Basic validation
        assert validate_header(state, block.header)
        assert validate_transaction_tree(state, block, db)
        # Process transactions
        #for tx in block.transactions:
            #apply_transaction(state, tx) #TODO: adaptar esta funcion
        # Post-finalize (ie. add the block header to the state for now)
        state.add_block_header(block.header)
    except (ValueError, AssertionError) as e:
        raise e
    return state


class Chain(object):

    def __init__(self, genesis=None, env=None,
                 new_head_cb=None, reset_genesis=False, localtime=None, max_history=1000, **kwargs):
        self.env = env or Env()
        # Initialize the state
        if 'head_hash' in self.db:  # new head tag
            self.state = self.mk_poststate_of_blockhash(
                self.db.get('head_hash'))
            self.state.executing_on_head = True
            print('Initializing chain from saved head, #%d (%s)' %
                  (self.state.prev_headers[0].number, encode_hex(self.state.prev_headers[0].hash)))
        elif genesis is None:
            raise Exception("Need genesis decl!")
        elif isinstance(genesis, State):
            assert env is None
            self.state = genesis
            self.env = self.state.env
            print('Initializing chain from provided state')
        elif "extraData" in genesis:
            self.state = state_from_genesis_declaration(
                genesis, self.env, executing_on_head=True)
            print('Initializing chain from provided genesis declaration')
        elif isinstance(genesis, dict):
            print('Initializing chain from new state based on alloc')
            self.state = mk_basic_state(genesis, {
                "number": kwargs.get('number', 0),
                "timestamp": kwargs.get('timestamp', 1467446877),
                "hash": kwargs.get('prevhash', '00' * 32)
                #TODO: add the rest of necessary fields for the genesis creation
            }, env=self.env)

        initialize(self.state)

        if isinstance(self.state.prev_headers[0], FakeHeader):
            header = self.state.prev_headers[0].to_block_header()
        else:
            header = self.state.prev_headers[0]

        self.genesis = Block(header)
        self.state.prev_headers[0] = header
        initialize_genesis_keys(self.state, self.genesis)

        assert self.env.db == self.state.db

        self.new_head_cb = new_head_cb
        assert self.state.block_number == self.state.prev_headers[0].number
        self.genesis = self.get_block_by_number(0)
        self.head_hash = self.state.prev_headers[0].hash
        self.time_queue = []
        self.parent_queue = {}
        self.localtime = time.time() if localtime is None else localtime
        self.max_history = max_history

    # Head (tip) of the chain
    @property
    def head(self):
        try:
            block_rlp = self.db.get(self.head_hash)
            if block_rlp == 'GENESIS':
                return self.genesis
            else:
                return rlp.decode(block_rlp, Block)
        except Exception:
            return None

    # Returns the post-state of the block
    def mk_poststate_of_blockhash(self, blockhash):
        if blockhash not in self.db:
            raise Exception("Block hash %s not found" % encode_hex(blockhash))

        block_rlp = self.db.get(blockhash)
        if block_rlp in ('GENESIS', b'GENESIS'):
            return State.from_snapshot(json.loads(
                self.db.get('GENESIS_STATE')), self.env)
        block = rlp.decode(block_rlp, Block)

        state = State(env=self.env)
        state.trie.root_hash = block.header.state_root
        update_block_env_variables(state, block)
        state.txindex = len(block.transactions)
        state.prev_headers = []
        b = block
        header_depth = state.config['PREV_HEADER_DEPTH']
        for i in range(header_depth + 1):
            state.prev_headers.append(b.header)
            try:
                b = rlp.decode(state.db.get(b.header.prevhash), Block)
            except Exception:
                break
        if i < header_depth:
            if state.db.get(b.header.prevhash) == 'GENESIS':
                jsondata = json.loads(state.db.get('GENESIS_STATE'))
                for h in jsondata["prev_headers"][:header_depth - i]:
                    state.prev_headers.append(dict_to_prev_header(h))
            else:
                raise Exception("Dangling prevhash")
        assert len(state.journal) == 0, state.journal
        return state

    # Gets the parent block of a given block
    def get_parent(self, block):
        if block.header.number == int(self.db.get('GENESIS_NUMBER')):
            return None
        return self.get_block(block.header.prevhash)

    # Gets the block with a given blockhash
    def get_block(self, blockhash):
        try:
            block_rlp = self.db.get(blockhash)
            if block_rlp == 'GENESIS':
                if not hasattr(self, 'genesis'):
                    self.genesis = rlp.decode(
                        self.db.get('GENESIS_RLP'), sedes=Block)
                return self.genesis
            else:
                return rlp.decode(block_rlp, Block)
        except Exception:
            return None

    # Add a record allowing you to later look up the provided block's
    # parent hash and see that it is one of its children
    def add_child(self, child):
        try:
            existing = self.db.get(b'child:' + child.header.prevhash)
        except Exception:
            existing = b''
        existing_hashes = []
        for i in range(0, len(existing), 32):
            existing_hashes.append(existing[i: i + 32])
        if child.header.hash not in existing_hashes:
            self.db.put(
                b'child:' + child.header.prevhash,
                existing + child.header.hash)

    # Gets the hash of the block with the given block number
    def get_blockhash_by_number(self, number):
        try:
            return self.db.get(b'block:%d' % number)
        except Exception:
            return None

    # Gets the block with the given block number
    def get_block_by_number(self, number):
        return self.get_block(self.get_blockhash_by_number(number))

    # Get the hashes of all known children of a given block
    def get_child_hashes(self, blockhash):
        o = []
        try:
            data = self.db.get(b'child:' + blockhash)
            for i in range(0, len(data), 32):
                o.append(data[i:i + 32])
            return o
        except Exception:
            return []

    # Get the children of a block
    def get_children(self, block):
        if isinstance(block, Block):
            block = block.header.hash
        if isinstance(block, BlockHeader):
            block = block.hash
        return [self.get_block(h) for h in self.get_child_hashes(block)]

    # This function should be called periodically so as to
    # process blocks that were received but laid aside because
    # they were received too early
    def process_time_queue(self, new_time=None):
        self.localtime = time.time() if new_time is None else new_time
        i = 0
        while i < len(
                self.time_queue) and self.time_queue[i].timestamp <= new_time:
            pre_len = len(self.time_queue)
            self.add_block(self.time_queue.pop(i))
            if len(self.time_queue) == pre_len:
                i += 1

    # Call upon receiving a block
    def add_block(self, block):
        now = self.localtime
        # Are we receiving the block too early?
        if block.header.timestamp > now:
            i = 0
            while i < len(
                    self.time_queue) and block.timestamp > self.time_queue[i].timestamp:
                i += 1
            self.time_queue.insert(i, block)
            return False
        # Is the block being added to the head?
        if block.header.prevhash == self.head_hash:
            self.state.deletes = []
            self.state.changed = {}
            #try:
            apply_block(self.state, block, self.env.db)
            #except (Exception):
                #print ("exception found int add_block (apply_block failed), returning False")
                #return False
            self.db.put(b'block:%d' % block.header.number, block.header.hash)
            # side effect: put 'score:' cache in db
            self.head_hash = block.header.hash
            for i, tx in enumerate(block.transactions):
                self.db.put(b'txindex:' +
                            tx.hash, rlp.encode([block.number, i]))
            assert self.get_blockhash_by_number(
                block.header.number) == block.header.hash
            changed = self.state.changed
        # Or is the block being added to a chain that is not currently the
        # head?
        elif block.header.prevhash in self.env.db:
            temp_state = self.mk_poststate_of_blockhash(block.header.prevhash)
            try:
                apply_block(temp_state, block, self.env.db)
            except (Exception):
                print ("exception found int add_block (apply_block in line 275 failed), returning False")
                return False
            changed = temp_state.changed
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print ("previous hash not found in parent queue, returning False")
            return False
        self.add_child(block)
        self.db.put('head_hash', self.head_hash)
        self.db.put(block.hash, rlp.encode(block))
        self.db.put(b'changed:' + block.hash,
                    b''.join([k.encode() if not isinstance(k, bytes) else k for k in list(changed.keys())]))
        print('Saved %d address change logs' % len(changed.keys()))
        self.db.commit()
        # Call optional callback
        if self.new_head_cb and block.header.number != 0:
            self.new_head_cb(block)
        # Are there blocks that we received that were waiting for this block?
        # If so, process them.
        if block.header.hash in self.parent_queue:
            for _blk in self.parent_queue[block.header.hash]:
                self.add_block(_blk)
            del self.parent_queue[block.header.hash]
        return True

    def __contains__(self, blk):
        if isinstance(blk, (str, bytes)):
            try:
                blk = rlp.decode(self.db.get(blk), Block)
            except Exception:
                return False
        try:
            o = self.get_block(self.get_blockhash_by_number(blk.number)).hash
            assert o == blk.hash
            return True
        except Exception:
            return False

    def has_block(self, block):
        return block in self

    def has_blockhash(self, blockhash):
        return blockhash in self.db

    def get_chain(self, frm=None, to=2**63 - 1):
        if frm is None:
            frm = int(self.db.get('GENESIS_NUMBER')) + 1
        chain = []
        for i in itertools.islice(itertools.count(), frm, to):
            h = self.get_blockhash_by_number(i)
            if not h:
                return chain
            chain.append(self.get_block(h))

    # Get block number and transaction index
    def get_tx_position(self, tx):
        if not isinstance(tx, (str, bytes)):
            tx = tx.hash
        if b'txindex:' + tx in self.db:
            data = rlp.decode(self.db.get(b'txindex:' + tx))
            return big_endian_to_int(data[0]), big_endian_to_int(data[1])
        else:
            return None

    def get_transaction(self, tx):
        print('Deprecated. Use get_tx_position')
        blknum, index = self.get_tx_position(tx)
        blk = self.get_block_by_number(blknum)
        return blk.transactions[index], blk, index

    # Get descendants of a block
    def get_descendants(self, block):
        output = []
        blocks = [block]
        while len(blocks):
            b = blocks.pop()
            blocks.extend(self.get_children(b))
            output.append(b)
        return output

    @property
    def db(self):
        return self.env.db

    # Get blockhashes starting from a hash and going backwards
    def get_blockhashes_from_hash(self, hash, max):
        block = self.get_block(hash)
        if block is None:
            return []

        header = block.header
        hashes = []
        for i in xrange(max):
            hash = header.prevhash
            block = self.get_block(hash)
            if block is None:
                break
            header = block.header
            hashes.append(header.hash)
            if header.number == 0:
                break
        return hashes

    @property
    def config(self):
        return self.env.config
