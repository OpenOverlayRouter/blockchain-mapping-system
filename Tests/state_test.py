from db import OverlayDB, RefcountDB
import rlp
import json
from state import State
from config import Env
from block import BlockHeader
from utils import decode_hex, big_endian_to_int, encode_hex, parse_as_bin, parse_as_int, normalize_address
import utils

def mk_basic_state(alloc, header=None, env=None, executing_on_head=False):
    env = env or Env()
    state = State(env=env, executing_on_head=executing_on_head)
    if not header:
        header = {
            "number": 0, "gas_limit": env.config['BLOCK_GAS_LIMIT'],
            "gas_used": 0, "timestamp": 1467446877, "difficulty": 1
        }
    h = BlockHeader()
    state.prev_headers = [h]

    for addr, data in alloc.items():
        addr = normalize_address(addr)
        assert len(addr) == 20
        if 'wei' in data:
            state.set_balance(addr, parse_as_int(data['wei']))
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'code' in data:
            state.set_code(addr, parse_as_bin(data['code']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))
        if 'storage' in data:
            for k, v in data['storage'].items():
                state.set_storage_data(addr, parse_as_bin(k), parse_as_bin(v))

    state.block_number = header["number"]
    state.gas_limit = header["gas_limit"]
    state.timestamp = header["timestamp"]
    state.block_difficulty = header["difficulty"]
    state.commit()
    return state

def accounts():
    k = utils.sha3(b'cow')
    v = utils.privtoaddr(k)
    k2 = utils.sha3(b'horse')
    v2 = utils.privtoaddr(k2)
    return k, v, k2, v2

k, v, k2, v2 = accounts()
alloc = {v: {"balance": 5}}
state = mk_basic_state(alloc, None)
state = mk_basic_state(alloc)
state.set_balance(v,32)
print(state.account_exists(v))
print(state.get_balance(v))