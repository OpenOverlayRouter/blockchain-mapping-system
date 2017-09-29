import rlp
from utils import sha3, sha3rlp, int_to_big_endian, parse_as_bin, ecsign, \
                  ecrecover_to_pub, to_string, pubkey_to_address, \
                  ip_to_bytes, bytes_to_ip, bytes_to_int, int_to_addr


def get_transaction_id(tx):
    return sha3(tx)


def get_transaction_from(tx):
    if isinstance(tx, str):
        tx = parse_as_bin(tx)
    vals = rlp.decode(tx)
    _tx = vals[:-3]
    category = bytes_to_int(vals[1])
    digest = hash_message(category, sha3rlp(_tx))
    v, r, s = vals[-3:]
    v = bytes_to_int(v)
    r = bytes_to_int(r)
    s = bytes_to_int(s)
    pubkey = ecrecover_to_pub(digest, v, r, s)
    return pubkey_to_address(pubkey)


def get_transaction_category(tx):
    vals = rlp.decode(tx)
    return vals[1]


def decode_transaction(tx):
    d = {}
    vals = rlp.decode(tx)
    d['id'] = get_transaction_id(tx).hex()
    d['from'] = get_transaction_from(tx).hex()
    d['to'] = vals[2].hex()
    d['nonce'] = vals[0].hex()
    d['category'] = vals[1].hex()
    if bytes_to_int(vals[1]) <= 1:
        d['value'] = bytes_to_ip(vals[3])
    else:
        d['metadata'] = [bytes_to_ip(v) if i%2 == 0 else v.hex()
                        for i, v in enumerate(vals[3])]
        d['value'] = bytes_to_ip(vals[4])
    d['time'] = vals[-4].hex()
    d['v'] = vals[-3].hex()
    d['r'] = vals[-2].hex()
    d['s'] = vals[-1].hex()
    return d


def hash_message(category, msg):
    prefix = b''
    if category == 0:
        prefix = b'\x19Allocate:\n'
    elif category == 1:
        prefix = b'\x19Delege:\n'
    elif category == 2:
        prefix = b'\x19MapServer:\n'
    elif category == 3:
        prefix = b'\x19Locator:\n'
    elif category == 4:
        prefix = b'\x19Revoke:\n'
    prefix += to_string(len(msg))
    return sha3(prefix+msg)


def encode_transaction(category, privkey, dest_address, value, time, metadata=None):
    nonce = int_to_big_endian(5) # get_nonce
    to = int_to_addr(dest_address)
    _value = ip_to_bytes(value)
    if category <= 1:
        tx = [nonce, category, to, _value, time]
    else:
        _metadata = []
        for data in metadata:
            _metadata.append(ip_to_bytes(data[0]))
            _metadata.append(parse_as_bin(data[1]))
        tx = [nonce, category, to, _metadata, _value, time]
    digest = hash_message(category, sha3rlp(tx))

    # get privkey?
    v, r, s = ecsign(digest, privkey)

    if category <= 1:
        tx = [nonce, category, to, _value, time, v, r, s]
    else:
        tx = [nonce, category, to, _metadata, _value, time, v, r, s]
    return rlp.encode(tx)



def main():
    # TESTS

    privkey = bytes.fromhex('2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c')
    address = 0x54450450e24286143a35686ad77a7c851ada01a0

    mapserver = [('172.16.10.1', '54dbb737eac5007103e729e9ab7ce64a6850a310'),
                 ('176.25.48.9', '89b44e4d3c81ede05d0f5de8d1a68f754d73d997')] 
    tx = encode_transaction(2, privkey, address, '192.152.0.0/16', 0, mapserver)
    print ("Tx:", tx.hex())
    print ("IP:", ip_to_bytes('192.152.0.0/16').hex())
    print ("Tx ID:", get_transaction_id(tx).hex())

    print ("Tx From:", get_transaction_from(tx).hex())
    from utils import privtoaddr
    print (privtoaddr(privkey).hex())    

    ip = ip_to_bytes('192.152.0.0/16')
    print ("Recover IP:", bytes_to_ip(ip))

    print(decode_transaction(tx))


if __name__ == "__main__":
    main()