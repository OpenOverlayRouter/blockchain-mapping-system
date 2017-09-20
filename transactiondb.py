from rlp.sedes import big_endian_int, binary
from utils import address
import keys

class Transaction():
    fields = [
        ('nonce', big_endian_int),
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