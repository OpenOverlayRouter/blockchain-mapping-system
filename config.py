from rlp.utils import decode_hex

import utils
from db import BaseDB, EphemDB
import copy


default_config = dict(
    # Genesis block difficulty
    GENESIS_DIFFICULTY=131072,
    # Genesis block gas limit
    GENESIS_GAS_LIMIT=3141592,
    # Genesis block prevhash, coinbase, nonce
    GENESIS_PREVHASH=b'\x00' * 32,
    GENESIS_COINBASE=b'\x00' * 20,
    GENESIS_NONCE=utils.zpad(utils.encode_int(42), 8),
    GENESIS_MIXHASH=b'\x00' * 32,
    GENESIS_TIMESTAMP=0,
    GENESIS_EXTRA_DATA=b'',
    GENESIS_INITIAL_ALLOC={},
    # Minimum gas limit
    MIN_GAS_LIMIT=5000,
    MAX_GAS_LIMIT=2 ** 63 - 1,
    # Gas limit adjustment algo:
    # block.gas_limit=block.parent.gas_limit * 1023/1024 +
    #                   (block.gas_used * 6 / 5) / 1024
    GASLIMIT_EMA_FACTOR=1024,
    GASLIMIT_ADJMAX_FACTOR=1024,
    BLOCK_GAS_LIMIT=4712388,
    BLKLIM_FACTOR_NOM=3,
    BLKLIM_FACTOR_DEN=2,
    # Network ID
    NETWORK_ID=1,
    ACCOUNT_INITIAL_NONCE=0,
)



class Env(object):

    def __init__(self, db=None, config=None, global_config=None):
        self.db = EphemDB() if db is None else db
        assert isinstance(self.db, BaseDB)
        self.config = config or dict(default_config)
        self.global_config = global_config or dict()