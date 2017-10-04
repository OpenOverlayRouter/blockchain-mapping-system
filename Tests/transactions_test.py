import utils
from transactions import Transaction
import rlp
from py_ecc.secp256k1 import privtopub
from netaddr import IPNetwork



priv = utils.random_privkey()
pub = privtopub(priv)
#self, nonce, to, value, type, data, v=0, r=0, s=0
tx = Transaction(0,"3282791d6fd713f1e94f4bfd565eaa78b3a0599d",IPNetwork("192.168.10/35"),0)