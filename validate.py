from own_exceptions import InvalidNonce, UnsignedTransaction, InvalidNonce, InsufficientBalance, InvalidTransaction


null_address = b'\xff' * 20


def rp(tx, what, actual, target):
    return '%r: %r actual:%r target:%r' % (tx, what, actual, target)


def validate_transaction(state, tx):
    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise UnsignedTransaction(tx)

    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);
    req_nonce = 0 if tx.sender == null_address else state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise InvalidNonce(rp(tx, 'nonce', tx.nonce, req_nonce))

    # (3) the sender account balance contains the value
    balance = state.get_balance(tx.sender)
    if not balance.in_own_ips(tx.ip_network):
        raise InsufficientBalance(
            rp(tx, 'balance', balance, tx.ip_network))

    return True