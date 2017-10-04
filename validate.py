import os
import rlp

from utils import normalize_address, hash32, trie_root, \
    big_endian_int, address, int256, encode_int, \
    safe_ord, int_to_addr, sha3, big_endian_to_int, \
    ascii_chr, bytearray_to_bytestr
from rlp.sedes import big_endian_int, Binary, binary, CountableList
from rlp.utils import decode_hex, encode_hex, ascii_chr
import utils
import trie
from ethereum import transactions
from trie import Trie
from securetrie import SecureTrie
from transactions import Transaction
from consensus_strategy import get_consensus_strategy
from specials import specials as default_specials
from config import Env, default_config
from db import BaseDB, EphemDB
from exceptions import InvalidNonce, InsufficientStartGas, UnsignedTransaction, \
    BlockGasLimitReached, InsufficientBalance, VerificationFailed, InvalidTransaction
import sys

def validate_transaction(state, tx):

    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise UnsignedTransaction(tx)

    assert config_fork_specific_validation(
        state.config, state.block_number, tx)

    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);
    req_nonce = 0 if tx.sender == null_address else state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise InvalidNonce(rp(tx, 'nonce', tx.nonce, req_nonce))

    # (3) the gas limit is no smaller than the intrinsic gas,
    # g0, used by the transaction;
    if tx.startgas < tx.intrinsic_gas_used:
        raise InsufficientStartGas(
            rp(tx, 'startgas', tx.startgas, tx.intrinsic_gas_used))

    # (4) the sender account balance contains at least the
    # cost, v0, required in up-front payment.
    total_cost = tx.value + tx.gasprice * tx.startgas

    if state.get_balance(tx.sender) < total_cost:
        raise InsufficientBalance(
            rp(tx, 'balance', state.get_balance(tx.sender), total_cost))

    # check block gas limit
    if state.gas_used + tx.startgas > state.gas_limit:
        raise BlockGasLimitReached(
            rp(tx, 'gaslimit', state.gas_used + tx.startgas, state.gas_limit))

    # EIP86-specific restrictions
    if tx.sender == null_address and (tx.value != 0 or tx.gasprice != 0):
        raise InvalidTransaction(
            "EIP86 transactions must have 0 value and gasprice")

return True