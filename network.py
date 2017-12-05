import sys
from datetime import datetime
from os import urandom

from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet.address import UNIXAddress
from twisted.internet import reactor, task
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import Protocol, Factory
from twisted.python.filepath import FilePath
from twisted.python import log

import messages
from transactions import Transaction
from block import Block, BlockHeader
import rlp
import random

GLOBAL_PORT = 5005
QUERY_PORT = 5006
P2P_PORT = 5007
HOST = '127.0.0.1'

BOOTSTRAP_NODES = ["127.0.0.2"]

PING_TIME = 300
BLOCK_CHUNK = 10

#log.startLogging(sys.stdout)

def _print(msg):
    print("[{}] {}".format(str(datetime.now()), msg))


class p2pProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.nodeid = None
        self.state = 'NODEID'
        self.pingcall = task.LoopingCall(self.sendPing)
        self.pong = False

    def connectionMade(self):
        self.transport.write(self.factory.nodeid.encode('utf-8') + b'\r\n')
        self.pingcall.start(PING_TIME, now=False)
    
    def connectionLost(self, reason):
        if self.nodeid is not None:
            _print("Connection Lost: {}".format(self.transport.getPeer()))
            try: self.pingcall.stop()
            except: pass
            del self.factory.peers[self.nodeid]
            del self.factory.peers_ip[self.nodeid]
        else:
            _print("Connection Error: {}".format(self.transport.getPeer()))

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            #print "STATE", self.state
            if self.state == 'NODEID':
                if self.factory.peers.get(line) is None:
                    self.nodeid = line
                    self.factory.peers[self.nodeid] = self
                    self.factory.peers_ip[self.nodeid] = self.transport.getPeer().host
                    _print("New Peer: {} {}".format(line, self.transport.getPeer()))
                    self.state = None
                else:
                    _print("Peer Already Known: {} {}".format(line, self.transport.getPeer()))
                    self.transport.loseConnection()
            elif self.state == 'LOCAL':
                self.factory.local.sendMsg(line)
                self.state = None
            else:
                try:
                    data = messages.read_envelope(line)
                    _print (data["msgtype"])
                    if data["msgtype"] == "ping":
                        #print self.transport.getPeer().host
                        self.sendPong()
                    elif data["msgtype"] == "pong":
                        #print self.transport.getPeer().host
                        self.pong = True
                    elif data["msgtype"] == "get_peers":
                        self.sendMsg(messages.set_peers(self.factory.peers_ip))
                    elif data["msgtype"] == "set_peers":
                        if self.factory.bootstrap == True:
                            print data.get("peers")
                            peers = data.get("peers")
                            for key in peers:
                                exists = self.factory.peers_ip.get(key)
                                if exists is None and key != self.factory.nodeid:
                                    point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT)
                                    #point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT, bindAddress=(HOST, 0))
                                    connectProtocol(point, p2pProtocol(self.factory))
                            self.sendGetNumBlocks()
                    elif data["msgtype"] == "set_tx":
                        try:
                            tx = rlp.decode(data["tx"].decode('hex'), Transaction)
                            self.factory.transactions.append(data["tx"])
                        except:
                            print "Wrong Tx"
                    elif data["msgtype"] == "set_block":
                        try:
                            block = rlp.decode(data["block"].decode('hex'), Block)
                            if self.factory.num_block == block.header.number - 1:
                                self.factory.blocks[block.header.number] = block
                                self.factory.num_block += 1
                            elif self.factory.bootstrap == True and block.header.number > self.factory.last_served_block:
                                if self.factory.blocks.get(block.header.number) is None:
                                    self.factory.blocks[block.header.number] = block
                            print block.header.number
                        except:
                            print "Wrong Block"
                    elif data["msgtype"] == "set_blocks":
                        if self.factory.bootstrap == True:
                            for b in data["blocks"]:
                                try:
                                    block = rlp.decode(b.decode('hex'), Block)
                                    if block.header.number > self.factory.last_served_block and \
                                    self.factory.blocks.get(block.header.number) is None:
                                        self.factory.blocks[block.header.number] = block
                                        print block.header.number
                                except:
                                    print "Wrong Block"
                    elif data["msgtype"] == "get_num_blocks":
                        self.sendMsg(messages.set_num_blocks(self.factory.num_block))
                    elif data["msgtype"] == "set_num_blocks":
                        if self.factory.bootstrap and (data["num"] >= self.factory.num_block):
                            self.factory.num_block = data["num"]
                            self.factory.ck_num = True
                    elif data["msgtype"] == "get_blocks":
                        num = data["num"]
                        chunk = data["chunk"]
                        blocks = []
                        for n in range(num, num+chunk):
                            exists = self.factory.blocks.get(n)
                            if exists is not None:
                                blocks.append(exists)
                        self.sendMsg(messages.set_blocks(blocks))
                    elif data["msgtype"] == "get_tx_pool":
                        self.sendMsg(messages.set_txs(self.factory.transactions))
                    elif data["msgtype"] == "set_txs":
                        txs = data["txs"]
                        for tx in txs:
                            try:
                                tx = rlp.decode(data["tx"].decode('hex'), Transaction)
                                self.factory.transactions.append(data["tx"])
                            except:
                                print "Wrong Tx"
                                
                except Exception as exception:
                    print "except", exception.__class__.__name__, exception
                    self.transport.loseConnection()
                #else:
                    #print (line)

    def sendMsg(self, msg):
        self.transport.write(msg)
    
    def sendPing(self):
        self.transport.write(messages.ping())
        self.pong = False
        d = task.deferLater(reactor, 3, self.checkPong)

    def checkPong(self):
        if self.pong == False:
            self.transport.loseConnection()

    def sendPong(self):
        self.transport.write(messages.pong())

    def sendGetPeers(self):
        self.sendMsg(messages.get_peers())

    def sendGetNumBlocks(self):
        print "sendGetNumBlocks"
        self.sendMsg(messages.get_num_blocks())


class localProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        if self.factory.local is None:
            self.factory.local = self
            _print("Local Connection")
        else:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.local = None
        _print("Local Connection Lost")

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            if line == b'quit':
                reactor.stop()
            try:
                data = messages.read_envelope(line)
                if data["msgtype"] == "get_tx":
                    if not self.factory.transactions:
                        self.sendMsg('None')
                    else:
                        self.sendMsg(self.factory.transactions.pop(0).encode('utf-8'))
                elif data["msgtype"] == "get_block":
                    if not self.factory.blocks:
                        self.sendMsg('None')
                    else:
                        self.sendMsg(self.factory.blocks.pop(0).encode('utf-8'))
                        self.factory.last_served_block += 1
                elif data["msgtype"] == "bootstrap":
                    self.sendMsg(self.factory.bootstrap)
                else:
                    for nodeid, address in self.factory.peers.items():
                        address.sendMsg(line)
            except Exception as exception:
                    print "except", exception.__class__.__name__, exception
                    self.transport.loseConnection()

    def sendMsg(self, msg):
        self.transport.write(msg + b'\r\n')


class myFactory(Factory):
    def __init__(self):
        self.nodeid = urandom(128//8).encode('hex')
        print ("NodeID: {}".format(self.nodeid))

    def startFactory(self):
        self.peers = {}
        self.peers_ip = {}
        self.num_block = 0
        self.last_served_block = 0
        self.blocks = {}
        self.transactions = []
        self.local = None
        self.bootstrap = True
        self.ck_num = False
        self.ck_num_blocks = task.LoopingCall(self.check_num_blocks)
        self.ck_bootstrap = task.LoopingCall(self.check_bootstrap)
        self.ck_tx = task.LoopingCall(self.check_tx)
    
    def stopFactory(self):
        pass
    
    def buildProtocol(self, addr):
        # TODO check port
        #print("hello", addr)
        if addr.host == "127.0.0.1":
            return localProtocol(self)
        return p2pProtocol(self)

    def check_num_blocks(self):
        if self.ck_num == True:
            self.ck_num_blocks.stop()
            self.ck_bootstrap.start(7, now=False)
            self.get_blocks()
    
    def check_bootstrap(self):
        if len(self.blocks) == (self.num_block - self.last_served_block):
            self.ck_bootstrap.stop()
            self.sendMsgRandomPeer(messages.get_tx_pool())
            self.bootstrap = False
            #self.ck_tx.start(2)
    
    def check_tx(self):
        pass

    def sendMsgRandomPeer(self, msg):
        nodeid, address = random.choice(list(self.peers.items()))
        print nodeid
        d = address.sendMsg(msg)

    def get_blocks(self):
        # TODO check last block
        self.last_served_block = 0
        last_block = self.last_served_block
        for i in range(last_block + 1, self.num_block, BLOCK_CHUNK):
            self.sendMsgRandomPeer(messages.get_blocks(i, BLOCK_CHUNK))
            d = task.deferLater(reactor, 5, self.check_blocks, i)

    def check_blocks(self, num):
        for i in range(num, num + BLOCK_CHUNK):
            if self.blocks.get(i) is None and i <= self.num_block:
                self.sendMsgRandomPeer(messages.get_block_num(i))
                d = task.deferLater(reactor, 5, self.check_block, i)
    
    def check_block(self, num):
        if self.blocks.get(num) is None:
            self.sendMsgRandomPeer(messages.get_block_num(num))
            d = task.deferLater(reactor, 5, self.check_block, num)



def printError(failure):
    print (failure.getErrorMessage())


def bootstrapProtocol(p):
    print "BOOTSTRAPING"
    p.factory.ck_num_blocks.start(1, now=False)
    p.sendGetPeers()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print ("Error: too many arguments")
        sys.exit(1)
    '''if len(sys.argv) == 2:
        HOST = sys.argv[1]'''

    try:
        factory = myFactory()
        endpoint_local = TCP4ServerEndpoint(reactor, QUERY_PORT)
        endpoint_local.listen(factory)
        _print("LISTEN: {}".format(QUERY_PORT))
        #endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT, interface=HOST)
        endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT)
        endpoint_p2p.listen(factory)
        _print("LISTEN P2P: {}".format(P2P_PORT))
    except CannotListenError:
        _print("ERROR: Port in use")
        sys.exit(1)

    # BootStrap Nodes
    _print ("Trying to connect to bootstrap hosts:")
    for host in BOOTSTRAP_NODES:
        if host != HOST:
            print ("[*] {}".format(host))
            point = TCP4ClientEndpoint(reactor, host, P2P_PORT)
            #point = TCP4ClientEndpoint(reactor, host, P2P_PORT, bindAddress=(HOST, 0))
            d = point.connect(factory)
            d.addCallback(bootstrapProtocol)
            d.addErrback(printError)

    reactor.run()
