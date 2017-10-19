from transactions import Transaction
import copy
from db import _EphemDB
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction
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

tx = Transaction(0,1,'54450450e24286143a35686ad77a7c851ada01a0', '192.152.0.0/16')
tx.sign(ks.privkey)
validate_transaction(state,tx)