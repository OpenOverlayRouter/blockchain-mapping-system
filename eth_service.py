import block
import transactiondb

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
    processed_elapsed = 0
    block



    def __init__(self, db):
        sce = self.config['eth']
        self.db = db

    def newBlock(self):
        self.block = block

    def addTransaction(self, transaction):
        self.block.transaction.append(transaction)
        encodedTransaction =
