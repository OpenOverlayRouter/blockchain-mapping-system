import json
import rlp

def make_envelope(msgtype, **kwargs):
    envelope = {'msgtype': msgtype}
    envelope.update(kwargs)
    return json.dumps(envelope).encode('utf-8') + b'\r\n'

def read_envelope(msg):
    return json.loads(msg)

def ping():
    return make_envelope("ping")

def pong():
    return make_envelope("pong")

def get_peers():
    return make_envelope("get_peers")

def set_peers(peers):
    kwargs = {"peers": peers}
    return make_envelope("set_peers", **kwargs)

def bootstrap():
    return make_envelope("bootstrap")

def set_tx(tx):
    rawtx = rlp.encode(tx).encode('hex')
    kwargs = {"tx": rawtx}
    return make_envelope("set_tx", **kwargs)

def get_tx(id):
    kwargs = {"id": id}
    return make_envelope("get_tx", **kwargs)

def get_tx_pool():
    return make_envelope("get_tx_pool")

def set_txs(txs):
    list_tx = []
    for tx in txs:
        rawtx = rlp.encode(tx).encode('hex')
        list_tx.append(rawtx)
    kwargs = {"txs": list_tx}
    return make_envelope("set_tx_pool", **kwargs)

def get_num_blocks():
    return make_envelope("get_num_blocks")

def set_num_blocks(num):
    kwargs = {"num": num}
    return make_envelope("set_num_blocks", **kwargs)

def get_block_num(num):
    kwargs = {"num": num}
    return make_envelope("get_block_num", **kwargs)

def set_block(block):
    rawblock = rlp.encode(block).encode('hex')
    kwargs = {"block": rawblock}
    return make_envelope("set_block", **kwargs)

def get_block():
    return make_envelope("get_block")

def get_blocks(num, chunk):
    kwargs = {"num": num,
              "chunk": chunk}
    return make_envelope("get_blocks", **kwargs)

def set_blocks(blocks):
    list_blocks = []
    for block in blocks:
        rawblock = rlp.encode(block).encode('hex')
        list_blocks.append(rawblock)
    kwargs = {"blocks": list_blocks}
    return make_envelope("set_blocks", **kwargs)

if __name__ == "__main__":
    print ping()
    print pong()
    print get_peers()
    print read_envelope(ping())
