from transactions import Transaction
import copy
from db import _EphemDB
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address


db = _EphemDB()
env = Env(_EphemDB())
chain = Chain(genesis=mk_genesis_data(env), env=env)
state = chain.state
address = "7719818983cb546d1badee634621dad4214cba25"
ks = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")

print(state.trie.root_hash.encode('HEX'))
balance = state.get_balance(address)
balance.remove_own_ips(IPNetwork('192.168.0.1/24'))
state.set_balance(address,balance)
state.commit()

print(state.trie.root_hash.encode('HEX'))
tx = Transaction(0,1,'54450450e24286143a35686ad77a7c851ada01a0', 0, '192.152.0.0/16')
tx.sign(ks.privkey)
apply_transaction(state,tx)