import rlp
from utils import sha3, sha3rlp, int_to_big_endian, parse_as_bin, ecsign, \
                  ecrecover_to_pub, to_string, pubkey_to_address, encode_int_len, \
                  ip_to_bytes, bytes_to_ip, bytes_to_int


def get_transaction_id(tx):
    return sha3(tx)


def get_transaction_from(tx):
    if isinstance(tx, str):
        tx = parse_as_bin(tx)
    vals = rlp.decode(tx)
    _tx = vals[:-3]
    digest = sha3rlp(_tx)
    digest = sha3(digest)
    v, r, s = vals[-3:]
    v = bytes_to_int(v)
    r = bytes_to_int(r)
    s = bytes_to_int(s)
    pubkey = ecrecover_to_pub(digest, v, r, s)
    return pubkey_to_address(pubkey)


def decode_transaction(tx):
    d = {}
    vals = rlp.decode(tx)
    d['id'] = get_transaction_id(tx).hex()
    d['from'] = get_transaction_from(tx).hex()
    d['to'] = vals[1].hex()
    d['nonce'] = vals[0].hex()
    d['value'] = bytes_to_ip(vals[2])
    d['v'] = vals[-3].hex()
    d['r'] = vals[-2].hex()
    d['s'] = vals[-1].hex()
    return d


def encode_transaction(privkey, dest_address, value):
    nonce = int_to_big_endian(5) # get_nonce
    to = encode_int_len(dest_address,20)
    _value = ip_to_bytes(value)
    tx = [nonce, to, _value]
    digest = sha3rlp(tx)
    digest = sha3(digest) # prefix?

    # get privkey?
    v, r, s = ecsign(digest, privkey)

    tx = [nonce, to, _value, v, r, s]
    return rlp.encode(tx)



def main():
    # TESTS

    privkey = bytes.fromhex('2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c')
    address = 0x54450450e24286143a35686ad77a7c851ada01a0

    tx = encode_transaction(privkey, address, '192.152.0.0/16')
    print ("Tx:", tx.hex())
    print ("IP:", ip_to_bytes('192.152.0.0/16').hex())
    print ("Tx ID:", get_transaction_id(tx).hex())

    print ("Tx From:", get_transaction_from(tx).hex())
    from utils import privtoaddr
    print (privtoaddr(privkey).hex())    

    ip = ip_to_bytes('192.152.0.0/16')
    print (ip)
    print (bytes_to_ip(ip))

    print(decode_transaction(tx))


if __name__ == "__main__":
    main()