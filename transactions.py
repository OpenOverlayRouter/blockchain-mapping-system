import rlp
from rlp.sedes import big_endian_int, BigEndianInt, binary, raw

from utils import (address, normalize_address, sha3, normalize_key, ecsign,
                   privtoaddr, ecrecover_to_pub, parse_as_bin, int_to_bytes,
                   ip_to_bytes, bytes_to_ip, encode_hex)
from own_exceptions import InvalidTransaction
from netaddr import IPNetwork, IPAddress, AddrFormatError

secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20

class Transaction(rlp.Serializable):

    fields = [
        ('nonce', big_endian_int),
        ('category', big_endian_int),
        ('to', address),
        ('value', binary),
        ('metadata', raw),
        ('time', big_endian_int),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]
    _sender = None

    def __init__ (self, nonce, category, to, value, 
                  metadata=b'', time=0, v=0, r=0, s=0):

        if category == 0 or category == 1:
            if metadata != b'':
                raise InvalidTransaction("Invalid Metadata")
        elif category == 2:
            if type(metadata) == list and len(metadata)%2==0:
                _metadata = []
                for i, elem in enumerate(metadata):
                    try:
                        if i % 2 == 0:
                            ip = IPAddress(elem)
                            _metadata.append(ip_to_bytes(str(ip)))
                        else:
                            addr = normalize_address(elem, allow_blank=True)
                            _metadata.append(addr)
                    except AddrFormatError:
                        if i % 2 == 0:
                            if len(elem) == 4:
                                try:
                                    ip = bytes_to_ip(elem)
                                    ip = IPAddress(ip)
                                    _metadata.append(ip_to_bytes(str(ip)))
                                except:
                                    raise InvalidTransaction("Invalid Metadata")
                            else:
                                raise InvalidTransaction("Invalid Metadata")
                metadata = _metadata
            else:
                raise InvalidTransaction("Invalid Metadata")
        elif category == 3:
            if type(metadata) == list and metadata:
                _metadata = []
                for elem in metadata:
                    try:
                        ip = IPAddress(elem)
                        _metadata.append(ip_to_bytes(str(ip)))
                    except AddrFormatError:
                        if len(elem) == 4:
                            try:
                                ip = bytes_to_ip(elem)
                                ip = IPAddress(ip)
                                _metadata.append(ip_to_bytes(str(ip)))
                            except:
                                raise InvalidTransaction("Invalid Metadata")
                        else:
                            raise InvalidTransaction("Invalid Metadata")
                metadata = _metadata
            else:
                raise InvalidTransaction("Invalid Metadata")
        
        to = normalize_address(to, allow_blank=True)

        try:
            ipnet = IPNetwork(value)
        except AddrFormatError:
            if len(value) == 5:
                try:
                    ipnet = bytes_to_ip(value)
                    ipnet = IPNetwork(ipnet)
                except:
                    raise InvalidTransaction("Invalid Value")
            else:
                raise InvalidTransaction("Invalid Value")
        value = ip_to_bytes(str(ipnet))

        super(
            Transaction, 
            self).__init__(
            nonce, 
            category, 
            to, 
            value,
            metadata, 
            time, 
            v, 
            r, 
            s)

    def hash_message(self, msg):
        prefix = b''
        if self.category == 0:
            prefix = b'Allocate:\n'
        elif self.category == 1:
            prefix = b'Delegate:\n'
        elif self.category == 2:
            prefix = b'MapServer:\n'
        elif self.category == 3:
            prefix = b'Locator:\n'
        return sha3(int_to_bytes(len(prefix)) + prefix +
                    int_to_bytes(len(msg)) + msg)

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
                if self.r >= secpk1n or self.s >= secpk1n or self.r == 0 or self.s == 0:
                    raise InvalidTransaction("Invalid signature values!")

                sighash = self.hash_message(sighash)
                pub = ecrecover_to_pub(sighash, self.v, self.r, self.s)
                if pub == b"\x00"*64:
                    raise InvalidTransaction(
                        "Invalid signature (zero privkey cannot sign)")
                self._sender = sha3(pub)[-20:]
        return self._sender

    @property
    def network_id(self):
        if self.r == 0 and self.s == 0:
            return self.v
        elif self.v in (27, 28):
            return None
        else:
            return ((self.v - 1) // 2) - 17

    def sign (self, key, network_id=None):
        if network_id is None:
            rawhash = sha3(rlp.encode(self, UnsignedTransaction))
        else:
            assert 1 <= network_id < 2**63 - 18
            rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                 :-3] + [network_id, b'', b''])
            rawhash = sha3(rlpdata)
        
        rawhash = self.hash_message(rawhash)
        key = normalize_key(key)
        self.v, self.r, self.s = ecsign(rawhash, key)
        if network_id is not None:
            self.v += 8 + network_id * 2
        
        self._sender = privtoaddr(key)
        return self

    @property
    def hash(self):
        return sha3(rlp.encode(self))

    @property
    def ip_network(self):
        return IPNetwork(bytes_to_ip(self.value))

    def to_dict(self):
        d = {}
        for name, _ in self.__class__.fields:
            d[name] = getattr(self, name)
            if name in ('to',):
                d[name] = '0x' + encode_hex(d[name])
            elif name in ('value',):
                d[name] = bytes_to_ip(str(d[name]))
            elif name in ('metadata',) and self.category==2:
                d[name] = [bytes_to_ip(v) if i%2 == 0 else encode_hex(v)
                           for i, v in enumerate(d[name])]
            elif name in ('metadata',) and self.category==3:
                d[name] = map(bytes_to_ip,d[name])
        d['sender'] = '0x' + encode_hex(self.sender)
        d['hash'] = '0x' + encode_hex(self.hash)
        return d

UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
