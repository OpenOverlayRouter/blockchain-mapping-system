import rlp
from utils import normalize_address, hash32, trie_root, \
    big_endian_int, address, int256, encode_int, \
    big_endian_to_int, int_to_addr, parse_as_bin, parse_as_int, \
    decode_hex, sha3, is_string, is_numeric, zpad
from rlp.sedes import big_endian_int, Binary, binary, CountableList
import utils
import trie
from trie import Trie
from securetrie import SecureTrie
from config import default_config, Env
from db import BaseDB, EphemDB, OverlayDB, RefcountDB
import copy
from account import Account
from trie import BLANK_NODE, BLANK_ROOT
import sys
from block import FakeHeader
from rlp.utils import encode_hex

STATE_DEFAULTS = {
    "txindex": 0,
    "block_number": 0,
    "block_coinbase": '\x00' * 20,
    "timestamp": 0,
    "prev_headers": []
}

class State():
    def __init__(self, root=b'', env=Env(), executing_on_head=False, **kwargs):
        self.env = env
        self.trie = SecureTrie(Trie(RefcountDB(self.db), root))
        self.txindex = STATE_DEFAULTS['txindex']
        self.block_number = STATE_DEFAULTS['block_number']
        self.block_coinbase = STATE_DEFAULTS['block_coinbase']
        self.timestamp = STATE_DEFAULTS['timestamp']
        self.prev_headers = STATE_DEFAULTS['prev_headers']
        self.journal = []
        self.cache = {}
        self.changed = {}
        self.executing_on_head = executing_on_head

    @property
    def db(self):
        return self.env.db

    @property
    def config(self):
        return self.env.config

    def get_block_hash(self, n):
        if self.block_number < n or n > 256 or n < 0:
            o = b'\x00' * 32
        else:
            o = self.prev_headers[n].hash if self.prev_headers[n] else b'\x00' * 32
        return o

    def add_block_header(self, block_header):
        self.prev_headers = [block_header] + self.prev_headers

    def get_and_cache_account(self, address):
        if address in self.cache:
            return self.cache[address]
        if self.executing_on_head and False:
            try:
                rlpdata = self.db.get(b'address:' + address)
            except KeyError:
                rlpdata = b''
        else:
            rlpdata = self.trie.get(address)
        if rlpdata != trie.BLANK_NODE:
            o = rlp.decode(rlpdata, Account, env=self.env, address=address)
        else:
            o = Account.blank_account(
                self.env, address, self.config['ACCOUNT_INITIAL_NONCE'])
        self.cache[address] = o
        o._mutable = True
        o._cached_rlp = None
        return o

    def get_balance(self, address):
        balance = self.get_and_cache_account(
            utils.normalize_address(address)).balance
        return utils.bin_to_object(balance)

    def get_nonce(self, address):
        return self.get_and_cache_account(utils.normalize_address(address)).nonce

    def set_and_journal(self, acct, param, val):
        # self.journal.append((acct, param, getattr(acct, param)))
        preval = getattr(acct, param)
        self.journal.append(lambda: setattr(acct, param, preval))
        setattr(acct, param, val)

    def set_balance(self, address, balance):
        balance = utils.object_to_bin(balance)
        acct = self.get_and_cache_account(utils.normalize_address(address))
        self.set_and_journal(acct, 'balance', balance)
        self.set_and_journal(acct, 'touched', True)

    def set_code(self, address, value):
        # assert is_string(value)
        acct = self.get_and_cache_account(utils.normalize_address(address))
        self.set_and_journal(acct, 'code', value)
        self.set_and_journal(acct, 'touched', True)

    def set_nonce(self, address, value):
        acct = self.get_and_cache_account(utils.normalize_address(address))
        self.set_and_journal(acct, 'nonce', value)
        self.set_and_journal(acct, 'touched', True)

    def increment_nonce(self, address):
        address = utils.normalize_address(address)
        acct = self.get_and_cache_account(address)
        newnonce = acct.nonce + 1
        self.set_and_journal(acct, 'nonce', newnonce)
        self.set_and_journal(acct, 'touched', True)

    def account_exists(self, address):
        a = self.get_and_cache_account(address)
        if a.deleted and not a.touched:
            return False
        if a.touched:
            return True
        else:
            return a.existent_at_start
        return o

    def delta_balance(self, address, value):
        address = utils.normalize_address(address)
        acct = self.get_and_cache_account(address)
        newbal = acct.balance + value
        self.set_and_journal(acct, 'balance', newbal)
        self.set_and_journal(acct, 'touched', True)

    def transfer_value(self, from_addr, to_addr, value):
        assert value >= 0
        if self.get_balance(from_addr) >= value:
            self.delta_balance(from_addr, -value)
            self.delta_balance(to_addr, value)
            return True
        return False

    def account_to_dict(self, address):
        return self.get_and_cache_account(utils.normalize_address(address)).to_dict()

    def commit(self, allow_empties=False):
        for addr, acct in self.cache.items():
            if acct.touched or acct.deleted:
                acct.commit()
                self.changed[addr] = True
                if self.account_exists(addr) or allow_empties:
                    rlp.encode(acct)
                    self.trie.update(addr, rlp.encode(acct))
                    if self.executing_on_head:
                        self.db.put(b'address:' + addr, rlp.encode(acct))
                else:
                    self.trie.delete(addr)
                    if self.executing_on_head:
                        try:
                            self.db.delete(b'address:' + addr)
                        except KeyError:
                            pass
        self.trie.deletes = []
        self.cache = {}
        self.journal = []

    def load_state(env, alloc):
        db = env.db
        state = SecureTrie(Trie(db, BLANK_ROOT))
        count = 0
        print("Start loading state from snapshot")
        for addr in alloc:
            print("[%d] loading account %s" % (count, addr))
            account = alloc[addr]
            acct = Account.blank_account(db, env.config['ACCOUNT_INITIAL_NONCE'])
            if len(account['storage']) > 0:
                t = SecureTrie(Trie(db, BLANK_ROOT))
                c = 0
                for k in account['storage']:
                    v = account['storage'][k]
                    enckey = zpad(decode_hex(k), 32)
                    t.update(enckey, decode_hex(v))
                    c += 1
                    if c % 1000 and len(db.db_service.uncommitted) > 50000:
                        print("%d uncommitted. committing..." % len(db.db_service.uncommitted))
                        db.commit()
                acct.storage = t.root_hash
            if account['nonce']:
                acct.nonce = int(account['nonce'])
            if account['balance']:
                acct.balance = int(account['balance'])
            if account['code']:
                acct.code = decode_hex(account['code'])
            state.update(decode_hex(addr), rlp.encode(acct))
            count += 1
        db.commit()
        return state

    # Creates a snapshot from a state
    def to_snapshot(self, root_only=False, no_prevblocks=False):
        snapshot = {}
        if root_only:
            # Smaller snapshot format that only includes the state root
            # (requires original DB to re-initialize)
            snapshot["state_root"] = '0x' + encode_hex(self.trie.root_hash)
        else:
            # "Full" snapshot
            snapshot["alloc"] = self.to_dict()
        # Save non-state-root variables
        for k, default in STATE_DEFAULTS.items():
            default = copy.copy(default)
            v = getattr(self, k)
            if is_numeric(default):
                snapshot[k] = str(v)
            elif isinstance(default, (str, bytes)):
                snapshot[k] = '0x' + encode_hex(v)
            elif k == 'prev_headers' and not no_prevblocks:
                snapshot[k] = [prev_header_to_dict(
                    h) for h in v[:self.config['PREV_HEADER_DEPTH']]]
            elif k == 'recent_uncles' and not no_prevblocks:
                snapshot[k] = {str(n): ['0x' + encode_hex(h)
                                        for h in headers] for n, headers in v.items()}
        return snapshot

    def to_dict(self):
        for addr in self.trie.to_dict().keys():
            self.get_and_cache_account(addr)
        return {encode_hex(addr): acct.to_dict()
                for addr, acct in self.cache.items()}

    # Creates a state from a snapshot
    @classmethod
    def from_snapshot(cls, snapshot_data, env, executing_on_head=False):
        state = State(env=env)
        if "alloc" in snapshot_data:
            for addr, data in snapshot_data["alloc"].items():
                if len(addr) == 40:
                    addr = decode_hex(addr)
                assert len(addr) == 20
                if 'balance' in data:
                    state.set_balance(addr, parse_as_int(data['balance']))
                if 'nonce' in data:
                    state.set_nonce(addr, parse_as_int(data['nonce']))
        elif "state_root" in snapshot_data:
            state.trie.root_hash = parse_as_bin(snapshot_data["state_root"])
        else:
            raise Exception(
                "Must specify either alloc or state root parameter")
        for k, default in STATE_DEFAULTS.items():
            default = copy.copy(default)
            v = snapshot_data[k] if k in snapshot_data else None
            if is_numeric(default):
                setattr(state, k, parse_as_int(v)
                if k in snapshot_data else default)
            elif is_string(default):
                setattr(state, k, parse_as_bin(v)
                if k in snapshot_data else default)
            elif k == 'prev_headers':
                if k in snapshot_data:
                    headers = [dict_to_prev_header(h) for h in v]
                else:
                    headers = default
                setattr(state, k, headers)
        if executing_on_head:
            state.executing_on_head = True
        state.commit()
        state.changed = {}
        return state

    @classmethod
    def from_snapshot(cls, snapshot_data, env, executing_on_head=False):
        state = State(env=env)
        if "alloc" in snapshot_data:
            for addr, data in snapshot_data["alloc"].items():
                if len(addr) == 40:
                    addr = decode_hex(addr)
                assert len(addr) == 20
                if 'balance' in data:
                    state.set_balance(addr, utils.bin_to_object(data['balance']))
                if 'nonce' in data:
                    state.set_nonce(addr, parse_as_int(data['nonce']))
        elif "state_root" in snapshot_data:
            state.trie.root_hash = parse_as_bin(snapshot_data["state_root"])
        else:
            raise Exception(
                "Must specify either alloc or state root parameter")
        for k, default in STATE_DEFAULTS.items():
            default = copy.copy(default)
            v = snapshot_data[k] if k in snapshot_data else None
            if is_numeric(default):
                setattr(state, k, parse_as_int(v)
                if k in snapshot_data else default)
            elif is_string(default):
                setattr(state, k, parse_as_bin(v)
                if k in snapshot_data else default)
            elif k == 'prev_headers':
                if k in snapshot_data:
                    headers = [dict_to_prev_header(h) for h in v]
                else:
                    headers = default
                setattr(state, k, headers)
        if executing_on_head:
            state.executing_on_head = True
        state.commit()
        state.changed = {}
        return state

    def snapshot(self):
        return (self.trie.root_hash, len(self.journal), {
            k: copy.copy(getattr(self, k)) for k in STATE_DEFAULTS})

    def revert(self, snapshot):
        h, L, auxvars = snapshot
        while len(self.journal) > L:
            try:
                lastitem = self.journal.pop()
                lastitem()
            except Exception as e:
                print(e)
        if h != self.trie.root_hash:
            assert L == 0
            self.trie.root_hash = h
            self.cache = {}
        for k in STATE_DEFAULTS:
            setattr(self, k, copy.copy(auxvars[k]))

def prev_header_to_dict(h):
    return {
        "hash": '0x' + encode_hex(h.hash),
        "number": str(h.number),
        "timestamp": str(h.timestamp)
    }

def dict_to_prev_header(h):
    return FakeHeader(hash=parse_as_bin(h['hash']),
                      number=parse_as_int(h['number']),
                      timestamp=parse_as_int(h['timestamp']))




BLANK_UNCLES_HASH = sha3(rlp.encode([]))
