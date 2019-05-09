import utils
from db import BaseDB, EphemDB


default_config = dict(
    # Genesis block prevhash, coinbase, nonce
    GENESIS_PREVHASH=b'\x00' * 32,
    GENESIS_COINBASE=b'\x00' * 20,
    GENESIS_NONCE=utils.zpad(utils.encode_int(42), 8),
    GENESIS_MIXHASH=b'\x00' * 32,
    GENESIS_TIMESTAMP=0,
    GENESIS_EXTRA_DATA=b'',
    GENESIS_INITIAL_ALLOC={},
    # Gas limit adjustment algo:
    # block.gas_limit=block.parent.gas_limit * 1023/1024 +
    #                   (block.gas_used * 6 / 5) / 1024
    #SHA-256 hash of 'IPchain is a blockchain developed at the Broadband Communications Research Group, used to study the feasability of a Proof of Stake blockchain to store and exchange IP addresses'    
    GENESIS_RANDOM_NO = 'a37172904aa905e74d00879fced7b721444ebdd2a598a1a5daf4726b66698782',
    GENESIS_GROUP_PUBLIC_KEY = '1 0x1449b385fbaed403e317430c8eced0d3b1f364ebfdd1ac9b1143e9a36def7651 0x181765270a148c0d455d20c1bbf78b6b2f9ed33f3ec8bbf96daff04bd4e88fde 0xf97fc07c06decd75f99a488d0731ef8117660b27a217df18a50c663b9b16b49 0x11c177b86813af3d9ea5bc38ba3107dc2cbc23675dc3c00c870b2eac4309181b',
    GENESIS_GROUP_SIGNATURE = '1 0xfd0d20db0a7f2f068fa57ad2ee40a3bb679fd3e24db0160eaf01e71b3358423 0x168a542a094ae73d8a1053abdde70bfa4b9969779bab2bab6548d1621ed33a6c',
    GASLIMIT_EMA_FACTOR=1024,
    GASLIMIT_ADJMAX_FACTOR=1024,
    BLOCK_GAS_LIMIT=4712388,
    BLKLIM_FACTOR_NOM=3,
    BLKLIM_FACTOR_DEN=2,
    # Network ID
    NETWORK_ID=1,
    ACCOUNT_INITIAL_NONCE=0,
    PREV_HEADER_DEPTH=256,
    
    
)



class Env(object):

    def __init__(self, db=None, config=None, global_config=None):
        self.db = EphemDB() if db is None else db
        assert isinstance(self.db, BaseDB)
        self.config = config or dict(default_config)
        self.global_config = global_config or dict()
