import rlp
from py_ecc.secp256k1 import privtopub
from utils import sha3_256
import utils
from utils import sha3, int_to_big_endian, ecsign
from ipaddress import IPv4Address


def bytes_to_int(data):
    return int.from_bytes(data, byteorder='big')


def int_to_bytes(integer, length):
    return integer.to_bytes(length=length, byteorder='big')


def hex_to_bytes(data):
    return bytes.fromhex(data)


def ip_to_bytes(addr):
    address, mask = addr.split('/')
    address = int(IPv4Address(address))
    return int_to_bytes(address, 4) + int_to_bytes(int(mask), 1)


def get_transaction_id(tx):
    return utils.sha3(tx)


def decode_transaction(tx):
    vals = rlp.decode(hex_to_bytes(tx))
    for v in vals:
        print(bytes_to_int(v))


def raw_transaction():  # Ethereum Example
    nonce = utils.int_to_big_endian(0)
    gasPrice = utils.int_to_big_endian(20000000000)
    gasLimit = utils.int_to_big_endian(100000)
    to = int_to_bytes(0x687422eEA2cB73B5d3e242bA5456b782919AFc85,20)
    value = utils.int_to_big_endian(1000)
    data = int_to_bytes(0xc0de,2)
    tx = [nonce, gasPrice, gasLimit, to, value, data]
    print(rlp.encode(tx).hex())
    h1 = utils.sha3(rlp.encode(tx))
    print("Raw hash:", h1.hex())
    key = bytes.fromhex('c0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0dec0de')
    v, r, s = utils.ecsign(h1, key)
    print('v:', hex(v), 'r:', hex(r), 's:', hex(s))
    tx = [nonce, gasPrice, gasLimit, to, value, data, v, r, s]
    print("raw tx:", rlp.encode(tx).hex())
    print("tx id:", utils.sha3(rlp.encode(tx)).hex())

    pubkey = utils.ecrecover_to_pub(h1, v,r,s)
    print(utils.sha3(pubkey).hex())
    p = privtopub(key)
    d = utils.int_to_big_endian(p[0])+utils.int_to_big_endian(p[1])
    print(utils.sha3(d).hex())


def encode_transaction(privkey, dest_address, value):
    nonce = int_to_big_endian(5) # get_nonce
    to = int_to_bytes(dest_address,20)
    _value = ip_to_bytes(value)
    tx = [nonce, to, _value]
    digest = sha3(rlp.encode(tx))
    # second hash

    # get privkey?
    v, r, s = ecsign(digest, privkey)
    print('v', hex(v), 'r', hex(r), 's', hex(s))

    #tx.append([v, r, s])
    tx = [nonce, to, _value, v, r, s]
    return rlp.encode(tx)



def main():
    # TESTS

    # https://github.com/ethereum/go-ethereum/issues/3731#issuecomment-283620075
    '''msgHash = 0x852daa74cc3c31fe64542bb9b8764cfb91cc30f9acf9389071ffb44a9eefde46
    r = 0xb814eaab5953337fed2cf504a5b887cddd65a54b7429d7b191ff1331ca0726b1
    s = 0x264de2660d307112075c15f08ba9c25c9a0cc6f8119aff3e7efb0a942773abb0
    v = 0x1b
    prefix = b'\x19Ethereum Signed Message:\n32' # prefix + len(msg)
    prefixedHash = utils.sha3(prefix+int_to_bytes(msgHash,32))
    pubkey = utils.ecrecover_to_pub(prefixedHash, v,r,s)
    print(pubkey.hex())
    print(utils.sha3_256(pubkey).hex())
    # PK should equal 0xa6fb229e9b0a4e4ef52ea6991adcfc59207c7711'''

    print('')
    privkey = bytes.fromhex('2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c')
    address = 0x54450450e24286143a35686ad77a7c851ada01a0

    print (encode_transaction(privkey, address, '192.152.0.0/16').hex())

    print ("IP:", ip_to_bytes('192.152.0.0/16').hex())

    print('')
    '''decode_transaction('f88b80881bc16d674ec80000830186a0941737b4e8e4101334b1b1\
                        965d3d739c41cc54f09680a4deaa59df0000000000000000000000\
                        00cbfdfb9fb838b9090a7fe1976ed98017632b44f178a00a484a59\
                        015d08e736f59edf07ffb32f73151fddec52885b1f29cbcfd7aac2\
                        039f842a3a63c2fb1771cd0495b93a4db94692d4733baa9e96c559\
                        ddc4ff600422')'''
    
    print('')
    '''print(get_transaction_id('f88b80881bc16d674ec80000830186a0941737b4e8e4101334b1b1\
                        965d3d739c41cc54f09680a4deaa59df0000000000000000000000\
                        00cbfdfb9fb838b9090a7fe1976ed98017632b44f178a00a484a59\
                        015d08e736f59edf07ffb32f73151fddec52885b1f29cbcfd7aac2\
                        039f842a3a63c2fb1771cd0495b93a4db94692d4733baa9e96c559\
                        ddc4ff600422').hex())'''
    
    #raw_transaction()


if __name__ == "__main__":
    main()