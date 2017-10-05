from db import OverlayDB, RefcountDB
import rlp
import json
from state import State
from config import Env
from block import BlockHeader
from utils import decode_hex, big_endian_to_int, encode_hex, parse_as_bin, parse_as_int, normalize_address, int_to_big_endian
import utils
import json
import random
from db import LevelDB

from account import Account

def mk_basic_state(alloc, header=None, env=None, executing_on_head=False):
    env = env or Env(LevelDB("./state"))
    state = State(root = "6c08c2bdb7c09eb5a2524e9ed8f3dac707c7b0f6ca2116a173989a5370f77340".decode('hex'),env=env, executing_on_head=executing_on_head)
    print(state.get_balance("3282791d6fd713f1e94f4bfd565eaa78b3a0599d"))
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
    state.timestamp = header["timestamp"]
    state.commit()

    env.db.commit()
    return state


with open('../genesis.json') as data_file:
    data = json.load(data_file)

print("INITIALAZING")

alloc = data['alloc']
state = mk_basic_state(alloc, None)
addresses = []
balances = []

tx = {}
for addr, data in alloc.items():
    addresses.append(addr)
    balances.append(parse_as_int(data['balance']))
    tx[addr] = 0

N = 50000
print("DOING SOME RANDOM TX...")
for i in range(N):
    randFrom = random.randint(0, len(addresses)-1)
    randTo = random.randint(0, len(addresses)-1)
    randBalance = random.randint(0, 5000)
    if(i%10000==0):
        print("...")
    balances[randFrom] = balances[randFrom] - parse_as_int(randBalance)
    balances[randTo] = balances[randTo] + parse_as_int(randBalance)
    state.increment_nonce(addresses[randFrom])
    state.transfer_value(addresses[randFrom],addresses[randTo],parse_as_int(randBalance))
    tx[addresses[randFrom]] = tx[addresses[randFrom]] - randBalance
    tx[addresses[randTo]] = tx[addresses[randTo]] + randBalance

state.commit()
print("TX PART FINISHED")
state.to_snapshot()
err = False
print("CHEKING VALUES...")
for i in range(0,len(addresses)):
    if(i%2000==0):
        print("...")
    if(balances[i] != state.get_balance(addresses[i])):
        print(addresses[i])
        print(balances[i])
        print(state.get_balance(addresses[i]))
        print ("TEST FAILED")
        print(tx[addresses[i]])
        err = True
        break;
if not err:
    print ("TEST PASSED")
