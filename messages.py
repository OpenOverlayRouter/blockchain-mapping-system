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

def set_peers(peers):
    kwargs = {"peers": peers}
    return make_envelope("set_peers", **kwargs)

def send_tx(tx):
    kwargs = {"tx": tx}
    return make_envelope("set_tx", **kwargs)

def get_tx():
    return make_envelope("get_tx")

def send_block(block):
    kwargs = {"block": block}
    return make_envelope("set_block", **kwargs)

def get_block():
    return make_envelope("get_block")

def get_blocks(height, chunk):
    kwargs = {"height": height,
              "chunk": chunk}
    return make_envelope("get_blocks", **kwargs)

if __name__ == "__main__":
    print ping()
    print pong()
    print get_peers()
    print read_envelope(ping())
