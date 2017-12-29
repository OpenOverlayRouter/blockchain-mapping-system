from state import State
from block import Block, BlockHeader
from utils import parse_as_bin, parse_as_int, normalize_address
from config import Env
from db import RefcountDB
import json
import rlp
from balance import Balance
from netaddr import IPNetwork
from utils import int_to_big_endian


def block_from_genesis_declaration(genesis_data, env):
    h = BlockHeader(timestamp=parse_as_int(genesis_data["timestamp"]), coinbase=parse_as_bin(genesis_data["coinbase"]), prevhash=parse_as_bin(genesis_data["parentHash"]))
    return Block(h, [])


def state_from_genesis_declaration(
        genesis_data, env, block=None, allow_empties=False, executing_on_head=False, pytricia={}):
    if block:
        assert isinstance(block, Block)
    else:
        block = block_from_genesis_declaration(genesis_data, env)

    state = State(env=env)
    #convert list to dictionary
    alloc_data = {}
    for elem in genesis_data["alloc"]:
        alloc_data[elem.keys()[0]] = elem[elem.keys()[0]]
    #print alloc_data    
    for addr, data in alloc_data.iteritems():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'balance' in data:
            balance = Balance(data['balance']['own_ips'])
            state.set_balance(addr, balance)
            for ip in data['balance']['own_ips']:
                pytricia[ip] = normalize_address(addr)
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

def mk_genesis_data(env):
    assert isinstance(env, Env)

    with open('genesis.json') as json_data:
        d = json.load(json_data)
        genesis_data = {
            "parentHash": d["parentHash"],
            "coinbase": d["coinbase"],
            "timestamp": d["timestamp"],
            "alloc": d["alloc"]
        }
    return genesis_data


# Block initialization state transition
def initialize(state):
    state.txindex = 0


def initialize_genesis_keys(state, genesis):
    db = state.db
    db.put('GENESIS_NUMBER', str(genesis.header.number))
    db.put('GENESIS_HASH', str(genesis.header.hash))
    db.put('GENESIS_STATE', json.dumps(state.to_snapshot()))
    genesis_rlp = rlp.encode(genesis,Block.exclude(['v', 'r', 's']))
    db.put('GENESIS_RLP', genesis_rlp)
    db.put(b'block:0', genesis.header.hash)
    db.put(b'state:' + genesis.header.hash, state.trie.root_hash)
    db.put(genesis.header.hash, 'GENESIS')
    db.commit()
