import json
import time
import itertools
from utils import big_endian_to_int
import rlp
from rlp.utils import encode_hex
from config import Env
from state import State, dict_to_prev_header
from block import Block, BlockHeader, FakeHeader, UnsignedBlock
from genesis_helpers import state_from_genesis_declaration, initialize, initialize_genesis_keys
from apply import apply_block, update_block_env_variables, validate_block, validate_transaction, verify_block_signature
from patricia_state import PatriciaState
import logging

databaseLog = logging.getLogger('Database')


class Chain(object):

    def __init__(self, genesis=None, env=None,
                 new_head_cb=None, reset_genesis=False, localtime=None, max_history=1000, **kwargs):
        self.env = env or Env()
        self.patricia = PatriciaState()
        self.patricia.from_db()  # TODO: test
        # Initialize the state
        if 'head_hash' in self.db:  # new head tag
            self.state = self.mk_poststate_of_blockhash(self.db.get('head_hash'))
            self.state.executing_on_head = True
            databaseLog.info('Initializing chain from saved head, #%d (%s)',self.state.prev_headers[0].number, encode_hex(self.state.prev_headers[0].hash))
        elif genesis is None:
            raise Exception("Need genesis decl!")
        elif isinstance(genesis, State):
            assert env is None
            self.state = genesis
            self.env = self.state.env
            databaseLog.info('Initializing chain from provided state')
        elif isinstance(genesis, dict):
            databaseLog.info('Initializing chain from new state based on alloc')
            diction = {}
            self.state = state_from_genesis_declaration(
                genesis, self.env, executing_on_head=True, pytricia=diction)

            for key in diction:
                self.patricia.set_value(str(key), str(diction[key]))
            self.patricia.to_db()
            reset_genesis = True
        assert self.env.db == self.state.db

        initialize(self.state)
        self.new_head_cb = new_head_cb

        if self.state.block_number == 0:
            assert self.state.block_number == self.state.prev_headers[0].number
        else:
            assert self.state.block_number == self.state.prev_headers[0].number

        if reset_genesis:
            if isinstance(self.state.prev_headers[0], FakeHeader):
                header = self.state.prev_headers[0].to_block_header()
            else:
                header = self.state.prev_headers[0]
            self.genesis = Block(header)
            self.state.prev_headers[0] = header
            initialize_genesis_keys(self.state, self.genesis)
        else:
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
        #try:
        block_rlp = self.db.get(blockhash)
        if block_rlp == 'GENESIS':
            if not hasattr(self, 'genesis'):
                self.genesis = rlp.decode(self.db.get('GENESIS_RLP'), sedes=Block.exclude(['v', 'r', 's']))
            return self.genesis
        else:
            return rlp.decode(block_rlp, Block)

    def get_head_block(self):
        try:
            block_rlp = self.db.get(self.head_hash)
            if block_rlp == 'GENESIS':
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
        hash = self.get_blockhash_by_number(number)
        block = self.get_block(hash)
        return block

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
        self.localtime = int(time.time()) if new_time is None else new_time
        i = 0
        while i < len(
                self.time_queue) and self.time_queue[i].timestamp <= new_time:
            pre_len = len(self.time_queue)
            self.add_block(self.time_queue.pop(i))
            if len(self.time_queue) == pre_len:
                i += 1

    def validate_transaction(self, tx):
        return validate_transaction(self.state,tx)

    def validate_block(self,block):
        return validate_block(self.state,block)

    def verify_block_signature(self,block,ip):
        return verify_block_signature(self.state,block,ip)

    # Call upon receiving a block
    def add_block(self, block):
        now = self.localtime
        # Are we receiving the block too early?
        try:
            validate_block(self.state,block)
        except (Exception):
            databaseLog.info("Exception found while validating block %s. Discarding...", block.hash.encode("HEX"))
            return False
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

            apply_block(self.state, block, self.patricia)

            self.patricia.to_db()

            self.db.put(b'block:%d' % block.header.number, block.header.hash)
            databaseLog.info('Adding block: number %d hash %s', block.header.number, block.header.hash.encode('HEX'))
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
                databaseLog.info("Block being added to a chain that is not currently the head")
                apply_block(temp_state, block)
            except (Exception):
                databaseLog.error("Exception found while applying block. Returning False")
                return False
            changed = temp_state.changed
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            databaseLog.debug("Previous hash not found in parent queue, returning False")
            return False
        self.add_child(block)
        self.db.put('head_hash', self.head_hash)
        self.db.put(block.hash, rlp.encode(block))
        self.db.put(b'changed:' + block.hash,
                    b''.join([k.encode() if not isinstance(k, bytes) else k for k in list(changed.keys())]))

        databaseLog.debug('Saved %d address change logs', len(changed.keys()))

        self.db.commit()

        if self.new_head_cb and block.header.number != 0:
            self.new_head_cb(block)

        self.state.block_number = block.header.number

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
        if isinstance(tx,str):
            tx = tx.decode("HEX")
        elif not isinstance(tx, bytes):
            tx = tx.hash
        if b'txindex:' + tx in self.db:
            data = rlp.decode(self.db.get(b'txindex:' + tx))
            return big_endian_to_int(data[0]), big_endian_to_int(data[1])
        else:
            return None

    def get_transaction(self, tx):
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
