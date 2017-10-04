from state import State
from block import Block, BlockHeader
from utils import encode_hex, \
    parse_as_bin, parse_as_int, normalize_address
from config import Env
from db import RefcountDB
import json
import rlp


def block_from_genesis_declaration(genesis_data, env):
    h = BlockHeader(timestamp=parse_as_int(genesis_data["timestamp"]))
    return Block(h, [])


def state_from_genesis_declaration(
        genesis_data, env, block=None, allow_empties=False, executing_on_head=False):
    if block:
        assert isinstance(block, Block)
    else:
        block = block_from_genesis_declaration(genesis_data, env)

    state = State(env=env)
    for addr, data in genesis_data["alloc"].items():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))
    #get_consensus_strategy(state.config).initialize(state, block)
    if executing_on_head:
        state.executing_on_head = True
    state.commit(allow_empties=allow_empties)
    rdb = RefcountDB(state.db)
    block.header.state_root = state.trie.root_hash
    state.changed = {}
    state.prev_headers = [block.header]
    return state

def mk_basic_state(alloc, header=None, env=None, executing_on_head=False):
    env = env or Env()
    state = State(env=env, executing_on_head=executing_on_head)
    if not header:
        header = {
            "number": 0, "timestamp": 1467446877
        }
    h = BlockHeader(timestamp=parse_as_int(header['timestamp']), number=parse_as_int(header['number']))
    state.prev_headers = [h]

    for addr, data in alloc.items():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))

    state.block_number = header["number"]
    state.timestamp = header["timestamp"]
    state.commit()
    return state

def mk_genesis_data(env, **kwargs):
    assert isinstance(env, Env)

    allowed_args = set([
        'start_alloc',
        'parent_hash',
        'coinbase',
        'timestamp',
        'extra_data',
        'nonce',
    ])
    assert set(kwargs.keys()).issubset(allowed_args)

    genesis_data = {
        "parentHash": kwargs.get('parent_hash', encode_hex(env.config['GENESIS_PREVHASH'])),
        "coinbase": kwargs.get('coinbase', encode_hex(env.config['GENESIS_COINBASE'])),
        "timestamp": kwargs.get('timestamp', 0),
        "extraData": kwargs.get('extra_data', encode_hex(env.config['GENESIS_EXTRA_DATA'])),
        "nonce": kwargs.get('nonce', encode_hex(env.config['GENESIS_NONCE'])),
    }
    return genesis_data


# Block initialization state transition
def initialize(state):
    config = state.config

    state.txindex = 0

    if state.is_DAO(at_fork_height=True):
        for acct in state.config['CHILD_DAO_LIST']:
            state.transfer_value(
                acct,
                state.config['DAO_WITHDRAWER'],
                state.get_balance(acct))


def initialize_genesis_keys(state, genesis, env):
    db = env.db
    db.put('GENESIS_NUMBER', str(genesis.header.number))
    db.put('GENESIS_HASH', str(genesis.header.hash))
    db.put('GENESIS_STATE', json.dumps(state)) #was meant to be state.to_snapshot(), saved just the state instead
    db.put('GENESIS_RLP', rlp.encode(genesis))
    db.put(b'block:0', genesis.header.hash)
    db.put(b'state:' + genesis.header.hash, state.trie.root_hash)
    db.put(genesis.header.hash, 'GENESIS')
    db.commit()