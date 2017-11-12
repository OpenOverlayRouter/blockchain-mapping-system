import rlp
import trie
from rlp.sedes import big_endian_int, Binary, binary, CountableList
from utils import hash32, trie_root, address, sha3
from rlp.utils import encode_hex
from config import default_config
from transactions import Transaction
from utils import address, sha3, normalize_key, ecsign, privtoaddr, ecrecover_to_pub, int_to_bytes, encode_hex, bytes_to_int, encode_int8
from own_exceptions import InvalidBlock

secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20

class BlockHeader(rlp.Serializable):
    fields = [
        ('prevhash', hash32),
        ('timestamp', big_endian_int),
        ('extra_data', binary),
        ('state_root', trie_root),
        ('tx_root', trie_root),
        ('number', big_endian_int),
        ('coinbase', address)
    ]

    def __init__(self,
                 prevhash=default_config['GENESIS_PREVHASH'],
                 state_root=trie.BLANK_ROOT,
                 tx_root=trie.BLANK_ROOT,
                 number=0,
                 timestamp=0,
                 coinbase=default_config['GENESIS_COINBASE'],
                 extra_data=''):
        self.prevhash = prevhash
        self.coinbase = coinbase
        self.state_root = state_root
        self.tx_root = tx_root
        self.number = number
        self.timestamp = timestamp
        self.extra_data = extra_data

    @property
    def hash(self):
        return sha3(rlp.encode(self))

    @property
    def hex_hash(self):
        return encode_hex(self.hash)


class FakeHeader():
    def __init__(self, hash='\x00' * 32, number=0, timestamp=0):
        self.hash = hash
        self.number = number
        self.timestamp = timestamp

    def to_block_header(self):
        return BlockHeader(
            number=self.number,
            timestamp=self.timestamp
        )


class Block(rlp.Serializable):
    fields = [
        ('header', BlockHeader),
        ('transactions', CountableList(Transaction)),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int)
    ]
    _signer = None

    def __init__(self, header, transactions=None):
        self.header = header
        self.transactions = transactions or []

    def sign(self, key, network_id=None):
        if network_id is None:
            rawhash = sha3(rlp.encode(self, UnsignedBlock))
        else:
            assert 1 <= network_id < 2 ** 63 - 18
            rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                 :-3] + [network_id, b'', b''])
            rawhash = sha3(rlpdata)

        key = normalize_key(key)
        self.v, self.r, self.s = ecsign(rawhash, key)
        if network_id is not None:
            self.v += 8 + network_id * 2

        self._signer = privtoaddr(key)
        return self

    @property
    def signer(self):
        if not self._signer:
            if self.r == 0 and self.s == 0:
                if self.header.number == 0:
                    pub = b"\x00" * 64
                    self._signer = sha3(pub)[-20:]
                    print("GENESIS BLOCK")
                self._signer = null_address
            else:
                if self.v in (27, 28):
                    vee = self.v
                    sighash = sha3(rlp.encode(self, UnsignedBlock))
                elif self.v >= 37:
                    vee = self.v - self.network_id * 2 - 8
                    assert vee in (27, 28)
                    rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                         :-3] + [self.network_id, '', ''])
                    sighash = sha3(rlpdata)
                if self.r >= secpk1n or self.s >= secpk1n or self.r == 0 or self.s == 0:
                    raise InvalidBlock("Invalid signature values!")

                pub = ecrecover_to_pub(sighash, self.v, self.r, self.s)
                if pub == b"\x00" * 64:
                    raise InvalidBlock(
                        "Invalid signature (zero privkey cannot sign)")
                self._signer = sha3(pub)[-20:]
        return self._signer

    def __getattribute__(self, name):
        try:
            return rlp.Serializable.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.header, name)

    @property
    def transaction_count(self):
        return len(self.transactions)

    def get_timestamp(self):
        return getattr(self.header, "timestamp")

UnsignedBlock = Block.exclude(['v', 'r', 's'])