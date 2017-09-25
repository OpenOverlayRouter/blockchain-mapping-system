from db import OverlayDB, RefcountDB
import rlp
import json
from state import State
from config import Env
from block import BlockHeader
from utils import decode_hex, big_endian_to_int, encode_hex, parse_as_bin, parse_as_int, normalize_address
import utils
import json
import random

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
        if 'balance' in data:
            state.set_balance(addr, parse_as_int(data['balance']))
        if 'nonce' in data:
            state.set_nonce(addr, parse_as_int(data['nonce']))


    state.block_number = header["number"]
    state.gas_limit = header["gas_limit"]
    state.timestamp = header["timestamp"]
    state.block_difficulty = header["difficulty"]
    state.commit()

    return state

with open('../genesis.json') as data_file:
    data = json.load(data_file)

alloc = data['alloc']
state = mk_basic_state(alloc, None)
addresses = []
balances = []

for addr, data in alloc.items():
    addresses.append(addr)
    balances.append(data['balance'])

N = 5000

for i in range(N):
    rand = random.randint(0, len(addresses)-1)