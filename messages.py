import json
import rlp

def make_envelope(msgtype, **kwargs):
    '''Encode JSON'''
    envelope = {"msgtype": msgtype}
    envelope.update(kwargs)
    return json.dumps(envelope).encode('utf-8') + b"\r\n"

def read_envelope(msg):
    '''Decode JSON'''
    return json.loads(msg)

def quit():
    '''Quit Network'''
    return make_envelope("quit")

def none():
    '''None'''
    return make_envelope("none")

def true():
    '''True'''
    return make_envelope("true")

def false():
    '''False'''
    return make_envelope("false")

def ping():
    '''Ping'''
    return make_envelope("ping")

def pong():
    '''Pong'''
    return make_envelope("pong")

def get_peers():
    '''Get Peers'''
    return make_envelope("get_peers")

def set_peers(peers):
    '''Set Peers
    peers: List (@IP)'''
    kwargs = {"peers": peers}
    return make_envelope("set_peers", **kwargs)

def bootstrap():
    '''Bootstrap'''
    return make_envelope("bootstrap")

def get_tx():
    '''Get Transaction'''
    return make_envelope("get_tx")

def get_tx_pool():
    '''Get Transaction Pool'''
    return make_envelope("get_tx_pool")

def set_tx(tx):
    '''Set Transaction
    tx: Transaction'''
    rawtx = rlp.encode(tx).encode('hex')
    kwargs = {"tx": rawtx}
    return make_envelope("set_tx", **kwargs)

def set_tx_pool(txs):
    '''Set Transactions
    txs: List (Raw Transaction)'''
    kwargs = {"txs": txs}
    return make_envelope("set_tx_pool", **kwargs)

def set_tx_local(tx):
    '''Set Transaction Local
    tx: Raw Transaction'''
    kwargs = {"tx": tx}
    return make_envelope("set_tx_local", **kwargs)

def get_num_blocks():
    '''Get Number of Blocks'''
    return make_envelope("get_num_blocks")

def set_num_blocks(num):
    '''Set Number of Blocks
    num: Integer'''
    kwargs = {"num": num}
    return make_envelope("set_num_blocks", **kwargs)

def get_block_num(num):
    '''Get Block Number
    num: Integer'''
    kwargs = {"num": num}
    return make_envelope("get_block_num", **kwargs)

def get_block():
    '''Get Block'''
    return make_envelope("get_block")

def get_blocks(num, chunk):
    '''Get Blocks
    num: Integer
    chunk: Integer'''
    kwargs = {"num": num,
              "chunk": chunk}
    return make_envelope("get_blocks", **kwargs)

def set_block(block):
    '''Set Block
    block: Block'''
    rawblock = rlp.encode(block).encode('hex')
    kwargs = {"block": rawblock}
    return make_envelope("set_block", **kwargs)

def set_blocks(blocks):
    '''Set Blocks
    blocks: List (Raw Blocks)'''
    kwargs = {"blocks": blocks}
    return make_envelope("set_blocks", **kwargs)

def set_block_local(block):
    '''Set Block Local
    block: Raw Block'''
    kwargs = {"block": block}
    return make_envelope("set_block_local", **kwargs)

def get_block_queries():
    '''Get Block Queries'''
    return make_envelope("get_block_queries")

def set_block_queries(blocks):
    '''Set Block Queries
    blocks: List (Blocks Num)'''
    kwargs = {"blocks": blocks}
    return make_envelope("set_block_queries", **kwargs)

def answer_block_queries(blocks):
    '''Answer Block Queries
    blocks: List(Blocks)'''
    list_blocks = []
    for block in blocks:
        rawblock = rlp.encode(block).encode('hex')
        list_blocks.append(rawblock)
    kwargs = {"blocks": list_blocks}
    return make_envelope("answer_block_queries", **kwargs)

def tx_pool_query():
    '''Transaction Pool Query'''
    return make_envelope("tx_pool_query")

def answer_tx_pool_query(txs):
    '''Answer Transaction Pool Query
    txs: List (Transactions)'''
    list_tx = []
    for tx in txs:
        rawtx = rlp.encode(tx).encode('hex')
        list_tx.append(rawtx)
    kwargs = {"txs": list_tx}
    return make_envelope("answer_tx_pool_query", **kwargs)


if __name__ == "__main__":
    print ping()
    print pong()
    print get_peers()
    print read_envelope(ping())
