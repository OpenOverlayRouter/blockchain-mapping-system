from rlp.sedes import big_endian_int, binary
from utils import address, normalize_address, sha3, ecrecover_to_pub, normalize_key, privtoaddr, ecsign
from exceptions import InvalidTransaction
import rlp
from netaddr import IPNetwork

secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20

class Transaction(rlp.Serializable):
    fields = [
        ('nonce', big_endian_int),
        ('to', address),
        ('value', IPNetwork),
        ('type', big_endian_int),
        #delegate = 0 (delegate with delegate permissions)
        #delegate = 1 (delegate without delegate permissions)
        #delegate = 2 (delegate whithout delegate permissions and with recovery option activated)
        ('data', binary),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]
    _sender = None

    def __init__(self, nonce, to, value, type, data, v=0, r=0, s=0):
        self.nonce = nonce
        to = normalize_address(to, allow_blank=True)
        self.to = to
        self.value = value
        self.type = type
        self.data = data
        self.v = v
        self.r = r
        self.s = s

        super(Transaction,self).__init__(nonce, to, value, type, data, v, r, s)

        def sign(self, key, network_id=None):
            if network_id is None:
                rawhash = sha3(rlp.encode(self, UnsignedTransaction))
            else:
                assert 1 <= network_id < 2 ** 63 - 18
                rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                     :-3] + [network_id, b'', b''])
                rawhash = sha3(rlpdata)

            key = normalize_key(key)

            self.v, self.r, self.s = ecsign(rawhash, key)
            if network_id is not None:
                self.v += 8 + network_id * 2

            self._sender = privtoaddr(key)

            return self

    @property
    def sender(self):
        if not self._sender:
            if self.r == 0 and self.s == 0:
                self._sender = null_address
            else:
                if self.v in (27, 28):
                    vee = self.v
                    sighash = sha3(rlp.encode(self, UnsignedTransaction))
                elif self.v >= 37:
                    vee = self.v - self.network_id * 2 - 8
                    assert vee in (27, 28)
                    rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                         :-3] + [self.network_id, '', ''])
                    sighash = sha3(rlpdata)
                else:
                    raise InvalidTransaction("Invalid V value")
                if self.r >= secpk1n or self.s >= secpk1n or self.r == 0 or self.s == 0:
                    raise InvalidTransaction("Invalid signature values!")
                pub = ecrecover_to_pub(sighash, vee, self.r, self.s)
                if pub == b"\x00" * 64:
                    raise InvalidTransaction(
                        "Invalid signature (zero privkey cannot sign)")
                self._sender = sha3(pub)[-20:]
        return self._sender


    @property
    def hash(self):
        return sha3(rlp.encode(self))

UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])