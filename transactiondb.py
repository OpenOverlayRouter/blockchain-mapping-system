from rlp.sedes import big_endian_int, binary
from utils import address

class Transaction():
    fields = [
        ('nonce', big_endian_int),
        ('ffrom', address),
        ('to', address),
        ('EID', big_endian_int),
        ('delegate', big_endian_int),
        #delegate = 0 (delegate with delegate permissions)
        #delegate = 1 (delegate without delegate permissions)
        #delegate = 2 (delegate whithout delegate permissions and with recovery option activated)
        ('data', binary),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]

    def __init__(self, nonce, ffrom, to, EID, delegate, data, v, r, s):
        self.nonce = nonce
        self.ffrom = ffrom
        self.to = to
        self.EID = EID
        self.delegate = delegate
        self.data = data
        self.v = v
        self.r = r
        self.s = s
