import rlp
from rlp.sedes import big_endian_int, BigEndianInt, binary, raw

from utils import (address, normalize_address, sha3, normalize_key, ecsign,
                   privtoaddr, ecrecover_to_pub, parse_as_bin, int_to_bytes,
                   encode_hex, bytes_to_int, encode_int8)
from own_exceptions import InvalidTransaction
from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address, Bytes

secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20

class Transaction(rlp.Serializable):

    fields = [
        ('nonce', big_endian_int),
        ('category', big_endian_int),
        ('to', address),
        ('afi', BigEndianInt(1)),
        ('value', binary),
        ('metadata', raw),
        ('time', big_endian_int),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]
    _sender = None

    def __init__ (self, nonce, category, to, afi, value, 
                  metadata=b'', time=0, v=0, r=0, s=0):

        if category == 0 or category == 1:
            if metadata != b'':
                raise InvalidTransaction("Invalid Metadata")
        elif category == 2:
            if type(metadata) == list and len(metadata) % 3 ==0:
                _metadata = []
                _afi = 0
                if type(metadata[0]) == bytes:
                    _bytes = True
                elif type(metadata[0]) == int:
                    _bytes = False
                else:
                    raise InvalidTransaction("Invalid Metadata")
                i = 0
                while i < len(metadata):
                    try:
                        if _bytes:
                            _afi = bytes_to_int(metadata[i])
                            _metadata.append(metadata[i])
                        else:
                            _afi = metadata[i]
                            _metadata.append(encode_int8(metadata[i]))
                        if _afi != 1 and _afi != 2:
                            raise InvalidTransaction("Invalid Metadata AFI")
                    except:
                        raise InvalidTransaction("Invalid Metadata AFI")
                    try:
                        if _bytes:
                            if _afi == 1:
                                ip = IPv4Address(Bytes(metadata[i+1]))
                            else:
                                ip = IPv6Address(Bytes(metadata[i+1]))
                            _metadata.append(bytes(ip.packed))
                            addr = normalize_address(metadata[i+2], allow_blank=True)
                            _metadata.append(addr)
                        else:
                            if _afi == 1:
                                ip = IPv4Address(metadata[i+1])
                            else:
                                ip = IPv6Address(metadata[i+1])
                            _metadata.append(bytes(ip.packed))
                            addr = normalize_address(metadata[i+2], allow_blank=True)
                            _metadata.append(addr)
                        i += 3
                    except:
                        raise InvalidTransaction("Invalid Metadata")
                metadata = _metadata
            else:
                raise InvalidTransaction("Invalid Metadata")

        elif category == 3:
            if type(metadata) == list and len(metadata) % 4 == 0:
                _metadata = []
                _afi = 0
                if type(metadata[0]) == bytes:
                    _bytes = True
                elif type(metadata[0]) == int:
                    _bytes = False
                else:
                    raise InvalidTransaction("Invalid Metadata")
                i = 0
                while i < len(metadata):
                    try:
                        if _bytes:
                            _afi = bytes_to_int(metadata[i])
                            _metadata.append(metadata[i])
                        else:
                            _afi = metadata[i]
                            _metadata.append(encode_int8(metadata[i]))
                        if _afi != 1 and _afi != 2:
                            raise InvalidTransaction("Invalid Metadata AFI")
                    except:
                        raise InvalidTransaction("Invalid Metadata AFI")
                    try:
                        if _bytes:
                            if _afi == 1:
                                ip = IPv4Address(Bytes(metadata[i+1]))
                            else:
                                ip = IPv6Address(Bytes(metadata[i+1]))
                            _metadata.append(bytes(ip.packed))
                            priority = bytes_to_int(metadata[i+2])
                            if priority < 0 or priority > 255:
                                raise InvalidTransaction("Invalid Metadata Priority")
                            _metadata.append(int_to_bytes(priority))
                            weight = bytes_to_int(metadata[i+3])
                            if weight < 0 or weight > 255:
                                raise InvalidTransaction("Invalid Metadata Weight")
                            _metadata.append(int_to_bytes(weight))
                        else:
                            if _afi == 1:
                                ip = IPv4Address(metadata[i+1])
                            else:
                                ip = IPv6Address(metadata[i+1])
                            _metadata.append(bytes(ip.packed))
                            priority = metadata[i+2]
                            if priority < 0 or priority > 255:
                                raise InvalidTransaction("Invalid Metadata Priority")
                            _metadata.append(int_to_bytes(priority))
                            weight = metadata[i+3]
                            if weight < 0 or weight > 255:
                                raise InvalidTransaction("Invalid Metadata Weight")
                            _metadata.append(int_to_bytes(weight))
                        i += 4
                    except:
                        raise InvalidTransaction("Invalid Metadata")
                metadata = _metadata
            else:
                raise InvalidTransaction("Invalid Metadata")
        else:
            raise InvalidTransaction("Invalid Category")
        
        to = normalize_address(to, allow_blank=True)

        if afi != 1 and afi != 2:
            raise InvalidTransaction("Invalid AFI")

        try:
            if afi == 1:
                ipnet = IPv4Network(value)
            else:
                ipnet = IPv6Network(value)
        except:
            if len(value) == 5:
                try:
                    ip = IPv4Address(Bytes(value[:4]))
                    ipnet = IPv4Network(str(ip) + '/' + str(bytes_to_int(value[4])))
                except:
                    raise InvalidTransaction("Invalid Value")
            elif len(value) == 17:
                try:
                    ip = IPv6Address(Bytes(value[:16]))
                    ipnet = IPv6Network(str(ip) + '/' + str(bytes_to_int(value[16])))
                except:
                    raise InvalidTransaction("Invalid Value")
            else:
                raise InvalidTransaction("Invalid Value")
        value = bytes(ipnet.packed) + encode_int8(ipnet.prefixlen)

        super(
            Transaction, 
            self).__init__(
            nonce, 
            category, 
            to,
            afi,
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
        if self.afi == 1:
            ip = IPv4Address(Bytes(self.value[:4]))
            ipnet = IPv4Network(str(ip) + '/' + str(bytes_to_int(self.value[4])))
        else:
            ip = IPv6Address(Bytes(self.value[:16]))
            ipnet = IPv6Network(str(ip) + '/' + str(bytes_to_int(self.value[16])))
        return str(ipnet)

    def to_dict(self):
        d = {}
        for name, _ in self.__class__.fields:
            d[name] = getattr(self, name)
            if name in ('to',):
                d[name] = '0x' + encode_hex(d[name])
            elif name in ('value',):
                if self.afi == 1:
                    ip = IPv4Address(Bytes(d[name][:4]))
                    net = IPv4Network(str(ip) + '/' + str(bytes_to_int(d[name][4])))
                    d[name] = str(net)
                else:
                    ip = IPv6Address(Bytes(d[name][:16]))
                    net = IPv6Network(str(ip) + '/' + str(bytes_to_int(d[name][16])))
                    d[name] = str(net)
            elif name in ('metadata',) and self.category==2:
                _metadata = []
                i = 0
                while i < len(d[name]):
                    _metadata.append(bytes_to_int(d[name][i]))
                    if _metadata[-1] == 1:
                        ip = IPv4Address(Bytes(d[name][i+1]))
                    else:
                        ip = IPv6Address(Bytes(d[name][i+1]))
                    _metadata.append(str(ip))
                    _metadata.append(encode_hex(d[name][i+2]))
                    i += 3
                d[name] = _metadata
            elif name in ('metadata',) and self.category==3:
                _metadata = []
                i = 0
                while i < len(d[name]):
                    _metadata.append(bytes_to_int(d[name][i]))
                    if _metadata[-1] == 1:
                        ip = IPv4Address(Bytes(d[name][i+1]))
                    else:
                        ip = IPv6Address(Bytes(d[name][i+1]))
                    _metadata.append(str(ip))
                    _metadata.append(bytes_to_int(d[name][i+2]))
                    _metadata.append(bytes_to_int(d[name][i+3]))
                    i += 4
                d[name] = _metadata
        d['sender'] = '0x' + encode_hex(self.sender)
        d['hash'] = '0x' + encode_hex(self.hash)
        return d

UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
