import copy
import time
import statistics
from collections import deque

import gevent
import gevent.lock
from gevent.queue import Queue
from gevent.event import AsyncResult

import rlp

from devp2p.protocol import BaseProtocol
from devp2p.service import WiredService

from block import Block
from ethereum.meta import make_head_candidate
from ethereum.pow.chain import Chain
from ethereum.pow.consensus import initialize, check_pow
from ethereum.config import Env
from ethereum.genesis_helpers import mk_genesis_data
from ethereum import config as ethereum_config
from ethereum.messages import apply_transaction, validate_transaction
from ethereum.transaction_queue import TransactionQueue
from ethereum.experimental.refcount_db import RefcountDB
from ethereum.slogging import get_logger
from ethereum.exceptions import InvalidTransaction, InvalidNonce, \
    InsufficientBalance, InsufficientStartGas, VerificationFailed
from transaction import Transaction
from ethereum.utils import encode_hex

from synchronizer import Synchronizer
import eth_protocol

from pyethapp import sentry
from pyethapp.dao import is_dao_challenge, build_dao_header

log = get_logger('eth.chainservice')



class ChainService(WiredService):

    """
    Manages the chain and requests to it.
    """
    # required by BaseService
    name = 'chain'
    default_config = dict(
        eth=dict(network_id=0, genesis='', pruning=-1),
        block=ethereum_config.default_config
    )

    # required by WiredService
    wire_protocol = eth_protocol.ETHProtocol  # create for each peer

    # initialized after configure:
    chain = None
    genesis = None
    synchronizer = None
    config = None
    block_queue_size = 1024
    #processed_gas = 0
    processed_elapsed = 0

    def __init__(self, app):
        self.config = app.config
        sce = self.config['eth']

        """""""""
        if int(sce['pruning']) >= 0:
            self.db = RefcountDB(app.services.db)
            if "I am not pruning" in self.db.db:
                raise RuntimeError(
                    "The database in '{}' was initialized as non-pruning. "
                    "Can not enable pruning now.".format(self.config['data_dir']))
            self.db.ttl = int(sce['pruning'])
            self.db.db.put("I am pruning", "1")
        else:
            self.db = app.services.db
            if "I am pruning" in self.db:
                raise RuntimeError(
                    "The database in '{}' was initialized as pruning. "
                    "Can not disable pruning now".format(self.config['data_dir']))
            self.db.put("I am not pruning", "1")
        """""""""

        if 'network_id' in self.db:
            db_network_id = self.db.get('network_id')
            if db_network_id != str(sce['network_id']):
                raise RuntimeError(
                    "The database in '{}' was initialized with network id {} and can not be used "
                    "when connecting to network id {}. Please choose a different data directory.".format(
                        self.config['data_dir'], db_network_id, sce['network_id']
                    )
                )

        else:
            self.db.put('network_id', str(sce['network_id']))
            self.db.commit()

        assert self.db is not None

        super(ChainService, self).__init__(app)
        log.info('initializing chain')
        coinbase = app.services.accounts.coinbase
        env = Env(self.db, sce['block'])

        genesis_data = sce.get('genesis_data', {})
        if not genesis_data:
            genesis_data = mk_genesis_data(env)
        self.chain = Chain(
            env=env, genesis=genesis_data, coinbase=coinbase,
            new_head_cb=self._on_new_head)
        header = self.chain.state.prev_headers[0]

        log.info('chain at', number=self.chain.head.number)
        if 'genesis_hash' in sce:
            assert sce['genesis_hash'] == self.chain.genesis.hex_hash, \
                "Genesis hash mismatch.\n  Expected: %s\n  Got: %s" % (
                    sce['genesis_hash'], self.chain.genesis.hex_hash)

        self.dao_challenges = dict()
        self.synchronizer = Synchronizer(self, force_sync=None)

        self.block_queue = Queue(maxsize=self.block_queue_size)
        # When the transaction_queue is modified, we must set
        # self._head_candidate_needs_updating to True in order to force the
        # head candidate to be updated.
        self.transaction_queue = TransactionQueue()
        self._head_candidate_needs_updating = True
        # Initialize a new head candidate.
        _ = self.head_candidate
        "self.min_gasprice = 20 * 10**9 # TODO: better be an option to validator service?"
        self.add_blocks_lock = False
        self.add_transaction_lock = gevent.lock.Semaphore()
        self.broadcast_filter = DuplicatesFilter()
        self.on_new_head_cbs = []
        self.newblock_processing_times = deque(maxlen=1000)

    @property
    def is_syncing(self):
        return self.synchronizer.synctask is not None

    @property
    def is_mining(self):
        """""""""
        if 'pow' in self.app.services:
            return self.app.services.pow.active
        if 'validator' in self.app.services:
            return self.app.services.validator.active
        return False
        """""""""
        return True #TODO: cambiar a versión definitiva; eliminar si sobra

    # TODO: Move to pyethereum
    def get_receipts(self, block):
        """"""""""
        # Receipts are no longer stored in the database, so need to generate
        # them on the fly here.
        temp_state = self.chain.mk_poststate_of_blockhash(block.header.prevhash)
        initialize(temp_state, block)
        for tx in block.transactions:
            apply_transaction(temp_state, tx)
        return temp_state.receipts
        """""""""""
        #TODO: no hay receipts, revisar clases donde se use esta función


    def _on_new_head(self, block):
        log.debug('new head cbs', num=len(self.on_new_head_cbs))
        self.transaction_queue = self.transaction_queue.diff(
            block.transactions)
        self._head_candidate_needs_updating = True
        for cb in self.on_new_head_cbs:
            cb(block)

    @property
    def head_candidate(self):
        if self._head_candidate_needs_updating:
            self._head_candidate_needs_updating = False
            # Make a copy of self.transaction_queue because
            # make_head_candidate modifies it.
            txqueue = copy.deepcopy(self.transaction_queue)
            self._head_candidate, self._head_candidate_state = make_head_candidate(
                self.chain, txqueue, timestamp=int(time.time()))
        return self._head_candidate

    def add_transaction(self, tx, origin=None, force_broadcast=False, force=False):
        if self.is_syncing:
            if force_broadcast:
                assert origin is None  # only allowed for local txs
                log.debug('force broadcasting unvalidated tx')
                self.broadcast_transaction(tx, origin=origin)
            return  # we can not evaluate the tx based on outdated state
        log.debug('add_transaction', locked=(not self.add_transaction_lock.locked()), tx=tx)
        assert isinstance(tx, Transaction)
        assert origin is None or isinstance(origin, BaseProtocol)

        if tx.hash in self.broadcast_filter:
            log.debug('discarding known tx')  # discard early
            return

        # validate transaction
        try:
            # Transaction validation for broadcasting. Transaction is validated
            # against the current head candidate.
            validate_transaction(self._head_candidate_state, tx)

            log.debug('valid tx, broadcasting')
            self.broadcast_transaction(tx, origin=origin)  # asap
        except InvalidTransaction as e:
            log.debug('invalid tx', error=e)
            return

        if origin is not None:  # not locally added via jsonrpc
            if not self.is_mining or self.is_syncing:
                log.debug('discarding tx', syncing=self.is_syncing, mining=self.is_mining)
                return
        """""""""
        if tx.gasprice >= self.min_gasprice:
            self.add_transaction_lock.acquire()
            self.transaction_queue.add_transaction(tx, force=force)
            self._head_candidate_needs_updating = True
            self.add_transaction_lock.release()
        else:
            log.info("too low gasprice, ignore", tx=encode_hex(tx.hash)[:8], gasprice=tx.gasprice)
        """""""""

    def check_header(self, header):
        return check_pow(self.chain.state, header)

    def add_block(self, t_block, proto):
        "adds a block to the block_queue and spawns _add_block if not running"
        self.block_queue.put((t_block, proto))  # blocks if full
        if not self.add_blocks_lock:
            self.add_blocks_lock = True  # need to lock here (ctx switch is later)
            gevent.spawn(self._add_blocks)

    def add_mined_block(self, block):
        log.debug('adding mined block', block=block)
        assert isinstance(block, Block)
        if self.chain.add_block(block):
            log.debug('added', block=block, ts=time.time())
            assert block == self.chain.head
            self.transaction_queue = self.transaction_queue.diff(block.transactions)
            self._head_candidate_needs_updating = True
            self.broadcast_newblock(block, chain_difficulty=self.chain.get_score(block))
            return True
        log.debug('failed to add', block=block, ts=time.time())
        return False

    def knows_block(self, block_hash):
        "if block is in chain or in queue"
        if self.chain.has_blockhash(block_hash):
            return True
        # check if queued or processed
        for i in range(len(self.block_queue.queue)):
            if block_hash == self.block_queue.queue[i][0].header.hash:
                return True
        return False

    def _add_blocks(self):
        log.debug('add_blocks', qsize=self.block_queue.qsize(),
                  add_tx_lock=self.add_transaction_lock.locked())
        assert self.add_blocks_lock is True
        self.add_transaction_lock.acquire()
        try:
            while not self.block_queue.empty():
                # sleep at the beginning because continue keywords will skip bottom
                gevent.sleep(0.001)

                t_block, proto = self.block_queue.peek()  # peek: knows_block while processing
                if self.chain.has_blockhash(t_block.header.hash):
                    log.warn('known block', block=t_block)
                    self.block_queue.get()
                    continue
                if not self.chain.has_blockhash(t_block.header.prevhash):
                    log.warn('missing parent', block=t_block, head=self.chain.head)
                    self.block_queue.get()
                    continue
                try:  # deserialize
                    st = time.time()
                    block = t_block.to_block()
                    elapsed = time.time() - st
                    log.debug('deserialized', elapsed='%.4fs' % elapsed, ts=time.time(),
                              gas_used=block.gas_used, gpsec=self.gpsec(block.gas_used, elapsed))
                except InvalidTransaction as e:
                    log.warn('invalid transaction', block=t_block, error=e, FIXME='ban node')
                    errtype = \
                        'InvalidNonce' if isinstance(e, InvalidNonce) else \
                        'NotEnoughCash' if isinstance(e, InsufficientBalance) else \
                        'OutOfGasBase' if isinstance(e, InsufficientStartGas) else \
                        'other_transaction_error'
                    sentry.warn_invalid(t_block, errtype)
                    self.block_queue.get()
                    continue
                except VerificationFailed as e:
                    log.warn('verification failed', error=e, FIXME='ban node')
                    sentry.warn_invalid(t_block, 'other_block_error')
                    self.block_queue.get()
                    continue

                # All checks passed
                log.debug('adding', block=block, ts=time.time())
                if self.chain.add_block(block):
                    now = time.time()
                    log.info('added', block=block, txs=block.transaction_count,
                             gas_used=block.gas_used)
                    if t_block.newblock_timestamp:
                        total = now - t_block.newblock_timestamp
                        self.newblock_processing_times.append(total)
                        avg = statistics.mean(self.newblock_processing_times)
                        med = statistics.median(self.newblock_processing_times)
                        max_ = max(self.newblock_processing_times)
                        min_ = min(self.newblock_processing_times)
                        log.info('processing time', last=total, avg=avg, max=max_, min=min_,
                                 median=med)
                    if self.is_mining:
                        self.transaction_queue = self.transaction_queue.diff(block.transactions)
                else:
                    log.warn('could not add', block=block)

                self.block_queue.get()  # remove block from queue (we peeked only)
        finally:
            self.add_blocks_lock = False
            self.add_transaction_lock.release()

    def gpsec(self, gas_spent=0, elapsed=0):
        if gas_spent:
            self.processed_gas += gas_spent
            self.processed_elapsed += elapsed
        return int(self.processed_gas / (0.001 + self.processed_elapsed))

    def broadcast_newblock(self, block, chain_difficulty=None, origin=None):
        if not chain_difficulty:
            assert self.chain.has_blockhash(block.hash)
            chain_difficulty = self.chain.get_score(block)
        assert isinstance(block, (eth_protocol.TransientBlock, Block))
        if self.broadcast_filter.update(block.header.hash):
            log.debug('broadcasting newblock', origin=origin)
            bcast = self.app.services.peermanager.broadcast
            bcast(eth_protocol.ETHProtocol, 'newblock', args=(block, chain_difficulty),
                  exclude_peers=[origin.peer] if origin else [])
        else:
            log.debug('already broadcasted block')

    def broadcast_transaction(self, tx, origin=None):
        assert isinstance(tx, Transaction)
        if self.broadcast_filter.update(tx.hash):
            log.debug('broadcasting tx', origin=origin)
            bcast = self.app.services.peermanager.broadcast
            bcast(eth_protocol.ETHProtocol, 'transactions', args=(tx,),
                  exclude_peers=[origin.peer] if origin else [])
        else:
            log.debug('already broadcasted tx')

    # wire protocol receivers ###########

    def on_wire_protocol_start(self, proto):
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_start', proto=proto)
        assert isinstance(proto, self.wire_protocol)
        # register callbacks
        proto.receive_status_callbacks.append(self.on_receive_status)
        proto.receive_newblockhashes_callbacks.append(self.on_newblockhashes)
        proto.receive_transactions_callbacks.append(self.on_receive_transactions)
        proto.receive_getblockheaders_callbacks.append(self.on_receive_getblockheaders)
        proto.receive_blockheaders_callbacks.append(self.on_receive_blockheaders)
        proto.receive_getblockbodies_callbacks.append(self.on_receive_getblockbodies)
        proto.receive_blockbodies_callbacks.append(self.on_receive_blockbodies)
        proto.receive_newblock_callbacks.append(self.on_receive_newblock)

        # send status
        head = self.chain.head
        proto.send_status(chain_difficulty=self.chain.get_score(head), chain_head_hash=head.hash,
                          genesis_hash=self.chain.genesis.hash)

    def on_wire_protocol_stop(self, proto):
        assert isinstance(proto, self.wire_protocol)
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_stop', proto=proto)

    def on_receive_status(self, proto, eth_version, network_id, chain_difficulty, chain_head_hash,
                          genesis_hash):
        log.debug('----------------------------------')
        log.debug('status received', proto=proto, eth_version=eth_version)

        if eth_version != proto.version:
            if ('eth', proto.version) in proto.peer.remote_capabilities:
                # if remote peer is capable of our version, keep the connection
                # even the peer tried a different version
                pass
            else:
                log.debug("no capable protocol to use, disconnect",
                          proto=proto, eth_version=eth_version)
                proto.send_disconnect(proto.disconnect.reason.useless_peer)
                return

        if network_id != self.config['eth'].get('network_id', proto.network_id):
            log.debug("invalid network id", remote_network_id=network_id,
                     expected_network_id=self.config['eth'].get('network_id', proto.network_id))
            raise eth_protocol.ETHProtocolError('wrong network_id')

        # check genesis
        if genesis_hash != self.chain.genesis.hash:
            log.warn("invalid genesis hash", remote_id=proto, genesis=genesis_hash.encode('hex'))
            raise eth_protocol.ETHProtocolError('wrong genesis block')

        # initiate DAO challenge
        self.dao_challenges[proto] = (DAOChallenger(self, proto), chain_head_hash, chain_difficulty)

    def on_dao_challenge_answer(self, proto, result):
        if result:
            log.debug("DAO challenge passed")
            _, chain_head_hash, chain_difficulty = self.dao_challenges[proto]

            # request chain
            self.synchronizer.receive_status(proto, chain_head_hash, chain_difficulty)
            # send transactions
            transactions = self.transaction_queue.peek()
            if transactions:
                log.debug("sending transactions", remote_id=proto)
                proto.send_transactions(*transactions)
        else:
            log.debug("peer failed to answer DAO challenge, stop.", proto=proto)
            if proto.peer:
                proto.peer.stop()
        del self.dao_challenges[proto]

    # transactions

    def on_receive_transactions(self, proto, transactions):
        "receives rlp.decoded serialized"
        log.debug('----------------------------------')
        log.debug('remote_transactions_received', count=len(transactions), remote_id=proto)
        for tx in transactions:
            self.add_transaction(tx, origin=proto)

    # blockhashes ###########

    def on_newblockhashes(self, proto, newblockhashes):
        """
        msg sent out if not the full block is propagated
        chances are high, that we get the newblock, though.
        """
        log.debug('----------------------------------')
        log.debug("recv newblockhashes", num=len(newblockhashes), remote_id=proto)
        assert len(newblockhashes) <= 256
        self.synchronizer.receive_newblockhashes(proto, newblockhashes)

    def on_receive_getblockheaders(self, proto, hash_or_number, block, amount, skip, reverse):
        hash_mode = 1 if hash_or_number[0] else 0
        block_id = encode_hex(hash_or_number[0]) if hash_mode else hash_or_number[1]
        log.debug('----------------------------------')
        log.debug("handle_getblockheaders", amount=amount, block=block_id)

        headers = []
        max_hashes = min(amount, self.wire_protocol.max_getblockheaders_count)

        if hash_mode:
            origin_hash = hash_or_number[0]
        else:
            if is_dao_challenge(self.config['eth']['block'], hash_or_number[1], amount, skip):
                log.debug("sending: answer DAO challenge")
                headers.append(build_dao_header(self.config['eth']['block']))
                proto.send_blockheaders(*headers)
                return
            try:
                origin_hash = self.chain.get_blockhash_by_number(hash_or_number[1])
            except KeyError:
                origin_hash = b''
        if not origin_hash or self.chain.has_blockhash(origin_hash):
            log.debug("unknown block")
            proto.send_blockheaders(*[])
            return

        unknown = False
        while not unknown and (headers) < max_hashes:
            if not origin_hash:
                break
            try:
                block_rlp = self.chain.db.get(last)
                if block_rlp == 'GENESIS':
                    #last = self.chain.genesis.header.prevhash
                    break
                else:
                    last = rlp.decode_lazy(block_rlp)[0][0]  # [head][prevhash]
            except KeyError:
                break
            assert origin
            headers.append(origin)

            if hash_mode:  # hash traversal
                if reverse:
                    for i in xrange(skip+1):
                        try:
                            header = self.chain.get_block(origin_hash)
                            origin_hash = header.prevhash
                        except KeyError:
                            unknown = True
                            break
                else:
                    origin_hash = self.chain.get_blockhash_by_number(origin.number + skip + 1)
                    try:
                        header = self.chain.get_block(origin_hash)
                        if self.chain.get_blockhashes_from_hash(header.hash, skip+1)[skip] == origin_hash:
                            origin_hash = header.hash
                        else:
                            unknown = True
                    except KeyError:
                        unknown = True
            else:  # number traversal
                if reverse:
                    if origin.number >= (skip+1):
                        number = origin.number - (skip + 1)
                        origin_hash = self.chain.get_blockhash_by_number(number)
                    else:
                        unknown = True
                else:
                    number = origin.number + skip + 1
                    try:
                        origin_hash = self.chain.get_blockhash_by_number(number)
                    except KeyError:
                        unknown = True

        log.debug("sending: found blockheaders", count=len(headers))
        proto.send_blockheaders(*headers)

    def on_receive_blockheaders(self, proto, blockheaders):
        log.debug('----------------------------------')
        if blockheaders:
            log.debug("on_receive_blockheaders", count=len(blockheaders), remote_id=proto,
                      first=encode_hex(blockheaders[0].hash), last=encode_hex(blockheaders[-1].hash))
        else:
            log.debug("recv 0 remote block headers, signifying genesis block")

        if proto in self.dao_challenges:
            self.dao_challenges[proto][0].receive_blockheaders(proto, blockheaders)
        else:
            self.synchronizer.receive_blockheaders(proto, blockheaders)

    # blocks ################

    def on_receive_getblockbodies(self, proto, blockhashes):
        log.debug('----------------------------------')
        log.debug("on_receive_getblockbodies", count=len(blockhashes))
        found = []
        for bh in blockhashes[:self.wire_protocol.max_getblocks_count]:
            try:
                found.append(self.chain.db.get(bh))
            except KeyError:
                log.debug("unknown block requested", block_hash=encode_hex(bh))
        if found:
            log.debug("found", count=len(found))
            proto.send_blockbodies(*found)

    def on_receive_blockbodies(self, proto, bodies):
        log.debug('----------------------------------')
        log.debug("recv block bodies", count=len(bodies), remote_id=proto)
        if bodies:
            self.synchronizer.receive_blockbodies(proto, bodies)

    def on_receive_newblock(self, proto, block, chain_difficulty):
        log.debug('----------------------------------')
        log.debug("recv newblock", block=block, remote_id=proto)
        self.synchronizer.receive_newblock(proto, block, chain_difficulty)