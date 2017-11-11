from own_exceptions import UnsignedTransaction, InvalidNonce, InsufficientBalance, UncategorizedTransaction, \
    InvalidCategory, InvalidBlockSigner, UnsignedBlock
import trie
from rlp.utils import encode_hex
from db import EphemDB
import rlp
from netaddr import IPAddress

null_address = b'\xff' * 20


def rp(tx, what, actual, target):
    return '%r: %r actual:%r target:%r' % (tx, what, actual, target)


def verify_block_signature(state, block, ip):
    try:
        if not block.signer:
            raise UnsignedBlock()
    except AttributeError:
        raise UnsignedBlock()

    if isinstance(ip, IPAddress):
        try:
            ip = IPAddress(ip)
        except Exception as e:
            raise e

    signer = block.signer
    if state.get_balance(signer).in_own_ips(ip):
        return True
    else:
        raise InvalidBlockSigner()


# Validate the transaction and check that it is correct
def validate_transaction(state, tx):
    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise UnsignedTransaction(tx)
    else:
        if tx.sender == null_address:
            raise UnsignedTransaction(tx)
    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);

    req_nonce = state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise InvalidNonce(rp(tx, 'nonce', tx.nonce, req_nonce))

    # (3) the sender account balance contains the value
    if hasattr(tx, 'category'):
        category = tx.category

        if category < 0 or category > 3:
            raise InvalidCategory(category)

        balance = state.get_balance(tx.sender)
        value = tx.ip_network

        if category == 0 or category == 1:
            if not balance.in_own_ips(value):
                raise InsufficientBalance(value)
        elif category == 2:
            pass
            # MapServer
        elif category == 3:
            pass
            # Locator
    else:
        raise UncategorizedTransaction(tx)

    return True


# Applies the transaction to the state
def apply_transaction(state, tx):
    validate_transaction(state, tx)
    category = tx.category
    if category == 0:  # allocate
        sender = tx.sender
        to = tx.to
        value = tx.ip_network

        sender_balance = state.get_balance(sender)

        affected = sender_balance.affected_delegated_ips(value)
        for add, ips in affected.iteritems():
            sender_balance.remove_delegated_ips(add, ips)
            received_balance = state.get_balance(add)
            received_balance.remove_received_ips(sender, ips)
            state.set_balance(add, received_balance)

        to_balance = state.get_balance(to)
        sender_balance.remove_own_ips(value)
        to_balance.add_own_ips(value)

        state.set_balance(to, to_balance)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)


    elif category == 1:  # delegate
        sender = tx.sender
        to = tx.to
        value = tx.ip_network

        sender_balance = state.get_balance(sender)

        affected = sender_balance.affected_delegated_ips(value)
        for add, ips in affected.iteritems():
            sender_balance.remove_delegated_ips(add, ips)
            received_balance = state.get_balance(add)
            received_balance.remove_received_ips(sender, ips)
            state.set_balance(add, received_balance)

        to_balance = state.get_balance(to)
        to_balance.add_received_ips(sender, value)
        sender_balance.add_delegated_ips(to, value)

        state.set_balance(to, to_balance)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)

    elif category == 2:  # MapServer
        sender = tx.sender
        value = tx.metadata

        sender_balance = state.get_balance(sender)
        sender_balance.set_map_server(value)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)

    elif category == 3:  # Locator
        sender = tx.sender
        value = tx.metadata
        sender_balance = state.get_balance(sender)
        sender_balance.set_locator(value)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)
    state.commit()
    return True


# Update block variables into the state
def update_block_env_variables(state, block):
    state.timestamp = block.header.timestamp
    state.block_number = block.header.number
    state.block_coinbase = block.header.coinbase


# Make the root of a receipt tree
def mk_transaction_sha(receipts):
    t = trie.Trie(EphemDB())
    for i, receipt in enumerate(receipts):
        t.update(rlp.encode(i), rlp.encode(receipt))
    return t.root_hash


# Validate that the transaction list root is correct
def validate_transaction_tree(state, block):
    if block.header.tx_root != mk_transaction_sha(block.transactions):
        raise ValueError("Transaction root mismatch: header %s computed %s, %d transactions" %
                         (
                         encode_hex(str(block.header.tx_root)), encode_hex(str(mk_transaction_sha(block.transactions))),
                         len(block.transactions)))
    return True


# Validate that the header is valid
def validate_header(state, header):
    parent = state.prev_headers[0]
    if parent:
        if header.prevhash != parent.hash:
            raise ValueError("Block's prevhash and parent's hash do not match: block prevhash %s parent hash %s" %
                             (encode_hex(header.prevhash), encode_hex(parent.hash)))
        if header.number != parent.number + 1:
            raise ValueError(
                "Block's number is not the successor of its parent number")
        if header.timestamp <= parent.timestamp:
            raise ValueError("Timestamp equal to or before parent")
        if header.timestamp >= 2 ** 256:
            raise ValueError("Timestamp waaaaaaaaaaayy too large")
    return True


def validate_block(state, block):
    assert validate_header(state, block.header)
    assert validate_transaction_tree(state, block)
    for tx in block.transactions:
        if not validate_transaction(state, tx):
            return False
    return True


# Applies the block-level state transition function
def apply_block(state, block):
    # Pre-processing and verification
    snapshot = state.snapshot()
    try:
        # Basic validation
        assert validate_header(state, block.header)
        assert validate_transaction_tree(state, block)
        # Process transactions
        for tx in block.transactions:
            apply_transaction(state, tx)
        # Post-finalize (ie. add the block header to the state for now)
        state.add_block_header(block.header)

    except (ValueError, AssertionError) as e:
        state.revert(snapshot)
        raise e
    return state
