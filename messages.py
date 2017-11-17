import json

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

def block_hashes():
    return make_envelope("block_hashes")

def get_block_hashes(hash, max_blocks):
    kwargs = {"hash": hash,
              "max_blocks":max_blocks}
    return make_envelope("getBlockHashes", **kwargs)

def blocks():
    return make_envelope("blocks")

def get_blocks(block_list):
    kwargs = {"block_list": block_list}
    return make_envelope("get_blocks", **kwargs)

if __name__ == "__main__":
    print ping()
    print pong()
    print get_peers()
    print block_hashes()
    print get_block_hashes(0x123456789, 30)
    print blocks()
    print get_blocks([0x1, 0x2, 0x3])
    print read_envelope(ping())
