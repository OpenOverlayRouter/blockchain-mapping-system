import sys
from datetime import datetime
from os import urandom
import socket
import random

from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.internet.endpoints import connectProtocol
#from twisted.internet.address import UNIXAddress
from twisted.internet import reactor, task
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import Protocol, Factory
#from twisted.python.filepath import FilePath
#from twisted.python import log

import messages
from transactions import Transaction
from block import Block, BlockHeader
import rlp

NOTIFY_PORT = 5005
QUERY_PORT = 5006
P2P_PORT = 5007
LOCALHOST = '127.0.0.1'

#BOOTSTRAP_NODE = "127.0.0.2"
BOOTSTRAP_NODE = "84.88.81.69"

PING_TIME = 300 # 5min
BLOCK_CHUNK = 10

#log.startLogging(sys.stdout)

def _print(msg):
    print("[{}] {}".format(str(datetime.now()), msg))
    sys.stdout.flush()

class p2pProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.nodeid = None
        self.state = 'NODEID'
        self.pingcall = task.LoopingCall(self.sendPing)
        self.pong = False
        self.buffer = ''

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
            if self.factory.block_queries.get(self) is not None:
                del self.factory.block_queries[self]
        else:
            _print("Connection Error: {}".format(self.transport.getPeer()))

    def dataReceived(self, data):
        self.buffer += data
        if self.buffer[-2:] == "\r\n":
            for line in self.buffer.splitlines():
                line = line.strip()
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
                else:
                    try:
                        data = messages.read_envelope(line)
                        _print (data["msgtype"])
                        #_print (data)
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
                                _print (data.get("peers"))
                                peers = data.get("peers")
                                for key in peers:
                                    exists = self.factory.peers_ip.get(key)
                                    if exists is None and key != self.factory.nodeid:
                                        point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT)
                                        #point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT, bindAddress=(LOCALHOST, 0))
                                        connectProtocol(point, p2pProtocol(self.factory))
                                self.sendGetNumBlocks()
                        elif data["msgtype"] == "get_num_blocks":
                            self.sendMsg(messages.set_num_blocks(self.factory.num_block))
                        elif data["msgtype"] == "set_num_blocks":
                            if self.factory.bootstrap:
                                if data["num"] > self.factory.num_block:
                                    self.factory.num_block = data["num"]
                                    #print data["num"]
                                self.factory.ck_num = True
                        elif data["msgtype"] == "set_tx":
                            try:
                                tx = rlp.decode(data["tx"].decode('hex'), Transaction)
                                self.factory.transactions.add(data["tx"])
                                if self.factory.notify is not None:
                                    self.factory.notify.sendMsg(b'1\r\n')
                            except:
                                _print ("Wrong Tx")
                        elif data["msgtype"] == "set_block":
                            try:
                                block = rlp.decode(data["block"].decode('hex'), Block)
                                if self.factory.num_block == block.header.number - 1:
                                    self.factory.blocks[block.header.number] = data["block"]
                                    self.factory.num_block += 1
                                    #print block.header.number
                                if self.factory.notify is not None:
                                    self.factory.notify.sendMsg(b'0\r\n')
                            except:
                                _print ("Wrong Block")
                        elif data["msgtype"] == "set_blocks":
                            if self.factory.bootstrap:
                                for b in data["blocks"]:
                                    try:
                                        block = rlp.decode(b.decode('hex'), Block)
                                        if block.header.number > self.factory.last_served_block and \
                                        self.factory.blocks.get(block.header.number) is None:
                                            self.factory.blocks[block.header.number] = b
                                        _print (block.header.number)
                                    except:
                                        _print ("Wrong Block")
                        elif data["msgtype"] == "get_block_num":
                            num = data["num"]
                            if num <= self.factory.last_served_block and not self.factory.bootstrap:
                                if self.factory.block_queries.get(self) is None:
                                    self.factory.block_queries[self] = set([num])
                                else:
                                    self.factory.block_queries[self].add(num)
                                if self.factory.notify is not None:
                                    self.factory.notify.sendMsg(b'2\r\n')
                            elif num <= self.factory.num_block:
                                block = self.factory.blocks.get(num)
                                if block is not None:
                                    self.sendMsg(messages.set_blocks([block]))
                        elif data["msgtype"] == "get_blocks":
                            num = data["num"]
                            chunk = data["chunk"]
                            blocks = []
                            notify = False
                            for n in range(num, num+chunk):
                                if n <= self.factory.last_served_block and not self.factory.bootstrap:
                                    if self.factory.block_queries.get(self) is None:
                                        self.factory.block_queries[self] = set([n])
                                        notify = True
                                    else:
                                        self.factory.block_queries[self].add(n)
                                        notify = True
                                elif n <= self.factory.num_block:
                                    block = self.factory.blocks.get(n)
                                    if block is not None:
                                        blocks.append(block)
                            if blocks:
                                self.sendMsg(messages.set_blocks(blocks))
                            if notify:
                                if self.factory.notify is not None:
                                        self.factory.notify.sendMsg(b'2\r\n')
                        elif data["msgtype"] == "get_tx_pool":
                            if not self.factory.bootstrap:
                                self.factory.tx_pool_query.add(self)
                                if self.factory.notify is not None:
                                    self.factory.notify.sendMsg(b'3\r\n')
                        elif data["msgtype"] == "set_tx_pool":
                            if self.factory.bootstrap and not self.factory.tx_pool:
                                txs = data["txs"]
                                for raw_tx in txs:
                                    try:
                                        tx = rlp.decode(raw_tx.decode('hex'), Transaction)
                                        self.factory.transactions.add(raw_tx)
                                    except:
                                        _print ("Wrong Tx")
                                self.factory.tx_pool = True                
                    except Exception as exception:
                        print "except", exception.__class__.__name__, exception
                        self.transport.loseConnection()
                    #else:
                        #print (line)
            self.buffer = ''

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
        self.sendMsg(messages.get_num_blocks())


class localProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.buffer = ''

    def connectionMade(self):
        port = self.transport.getHost().port
        if port == QUERY_PORT:
            if self.factory.local is None:
                self.factory.local = self
                _print("Local Connection")
            else:
                self.transport.loseConnection()
        elif port == NOTIFY_PORT:
            if self.factory.notify is None:
                self.factory.notify = self
                _print("Notify Connection")
                if self.factory.blocks:
                    self.sendMsg(b'0\r\n')
                elif self.factory.transactions:
                    self.sendMsg(b'1\r\n')
                elif self.factory.block_queries:
                    self.sendMsg(b'2\r\n')
                elif self.factory.tx_pool_query:
                    self.sendMsg(b'3\r\n')
                self.sendMsg(b'-1\r\n')
            else:
                self.transport.loseConnection()
        '''if self.factory.local is None:
            self.factory.local = self
            _print("Local Connection")
        else:
            self.transport.loseConnection()'''

    def connectionLost(self, reason):
        self.factory.local = None
        _print("Local Connection Lost")

    def dataReceived(self, data):
        self.buffer += data
        if self.buffer[-2:] == "\r\n":
            for line in self.buffer.splitlines():
                line = line.strip()
                try:
                    data = messages.read_envelope(line)
                    #print data
                    if data["msgtype"] == "quit":
                        reactor.stop()
                    elif data["msgtype"] == "bootstrap":
                        if self.factory.bootstrap:
                            self.sendMsg(messages.true())
                        else:
                            self.sendMsg(messages.false())
                    elif data["msgtype"] == "get_tx":
                        if not self.factory.transactions:
                            self.sendMsg(messages.none())
                        else:
                            tx = self.factory.transactions.pop().encode('utf-8')
                            self.sendMsg(messages.set_tx_local(tx))
                    elif data["msgtype"] == "set_tx":
                        self.sendPeers(line + '\r\n')
                    elif data["msgtype"] == "get_block":
                        if not self.factory.blocks:
                            self.sendMsg(messages.none())
                        else:
                            block = self.factory.blocks.get(self.factory.last_served_block + 1)
                            if block:
                                self.sendMsg(messages.set_block_local(block.encode('utf-8')))
                                self.factory.last_served_block += 1
                            else:
                                self.sendMsg(messages.none())
                    elif data["msgtype"] == "set_block":
                        self.sendPeers(line + '\r\n')
                        self.factory.num_block += 1
                        self.factory.last_served_block += 1
                    elif data["msgtype"] == "get_block_queries":
                        if not self.factory.block_queries:
                            self.sendMsg(messages.none())
                        else:
                            blocks = set()
                            for v in self.factory.block_queries.values():
                                blocks.update(v)
                                if len(blocks) >= 10: # Max Blocks Query
                                    break
                            self.sendMsg(messages.set_block_queries(list(blocks)[:10]))
                    elif data["msgtype"] == "answer_block_queries":
                        peers = self.factory.block_queries.keys()
                        for peer in peers:
                            blocks = []
                            for b in data["blocks"]:
                                block = rlp.decode(b.decode('hex'), Block)
                                if block.header.number in self.factory.block_queries[peer]:
                                    blocks.append(b)
                                    self.factory.block_queries[peer].discard(block.header.number)
                            if not self.factory.block_queries[peer]:
                                del self.factory.block_queries[peer]
                            peer.sendMsg(messages.set_blocks(blocks))
                    elif data["msgtype"] == "tx_pool_query":
                        if not self.factory.tx_pool_query:
                            self.sendMsg(messages.false())
                        else:
                            self.sendMsg(messages.true())
                    elif data["msgtype"] == "answer_tx_pool_query":
                        while self.factory.tx_pool_query:
                            peer = self.factory.tx_pool_query.pop()
                            peer.sendMsg(messages.set_tx_pool(data["txs"]))
                    '''else:
                        for nodeid, address in self.factory.peers.items():
                            address.sendMsg(line + '\r\n')'''
                except Exception as exception:
                        print "except", exception.__class__.__name__, exception
                        self.transport.loseConnection()
            self.buffer = ''

    def sendMsg(self, msg):
        self.transport.write(msg)
    
    def sendPeers(self, msg):
        for nodeid, address in self.factory.peers.items():
            address.sendMsg(msg)


class myFactory(Factory):
    def __init__(self, last_block):
        self.nodeid = urandom(128//8).encode('hex')
        _print ("NodeID: {}".format(self.nodeid))
        self.num_block = last_block
        self.last_served_block = last_block

    def startFactory(self):
        self.peers = {}
        self.peers_ip = {}
        self.blocks = {}
        self.transactions = set()
        self.local = None
        self.notify = None
        self.bootstrap = False
        self.ck_num = False
        self.ck_num_blocks = task.LoopingCall(self.check_num_blocks)
        self.ck_blocks = task.LoopingCall(self.check_all_blocks)
        self.tx_pool = False
        self.ck_tx = task.LoopingCall(self.check_tx)
        self.block_queries = {}
        self.tx_pool_query = set()
    
    def stopFactory(self):
        pass
    
    def buildProtocol(self, addr):
        if addr.host == "127.0.0.1":
            return localProtocol(self)
        return p2pProtocol(self)

    def check_num_blocks(self):
        if self.ck_num == True:
            self.ck_num_blocks.stop()
            self.ck_blocks.start(7, now=False)
            self.get_blocks()
    
    def check_all_blocks(self):
        if len(self.blocks) == (self.num_block - self.last_served_block):
            self.ck_blocks.stop()
            self.sendMsgRandomPeer(messages.get_tx_pool())
            self.ck_tx.start(3, now=False)
    
    def check_tx(self):
        if self.tx_pool == True:
            self.ck_tx.stop()
            self.bootstrap = False
        else:
            self.sendMsgRandomPeer(messages.get_tx_pool())

    def sendMsgRandomPeer(self, msg):
        nodeid, address = random.choice(list(self.peers.items()))
        #print 'sendMsgRandomPeer', nodeid
        d = address.sendMsg(msg)

    def get_blocks(self):
        last_block = self.last_served_block
        for i in range(last_block + 1, self.num_block + 1, BLOCK_CHUNK):
            if (i + BLOCK_CHUNK - 1) > self.num_block:
                self.sendMsgRandomPeer(messages.get_blocks(i, self.num_block % BLOCK_CHUNK))
                #print "getblocks 1", i, self.num_block % BLOCK_CHUNK
            else:
                self.sendMsgRandomPeer(messages.get_blocks(i, BLOCK_CHUNK))
                #print "getblocks 2", i, BLOCK_CHUNK
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
    reactor.stop()


def bootstrapProtocol(p):
    _print ("BOOTSTRAPING")
    p.factory.bootstrap = True
    p.factory.ck_num_blocks.start(1, now=False)
    p.sendGetPeers()

def my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        #s.connect(('10.255.255.255', 1))
        s.connect((BOOTSTRAP_NODE, 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("Usage: python network.py LAST_BLOCK_NUM")
        sys.exit(1)
    elif len(sys.argv) == 3:
        LOCALHOST = sys.argv[2]
    elif len(sys.argv) > 3:
        print ("Error: too many arguments")
        sys.exit(1)

    try:
        factory = myFactory(int(sys.argv[1]))
        endpoint_query = TCP4ServerEndpoint(reactor, QUERY_PORT)
        endpoint_query.listen(factory)
        _print("LISTEN QUERY: {}".format(QUERY_PORT))
        endpoint_notify = TCP4ServerEndpoint(reactor, NOTIFY_PORT)
        endpoint_notify.listen(factory)
        _print("LISTEN NOTIFY: {}".format(NOTIFY_PORT))
        endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT)
        #endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT, interface=LOCALHOST)
        endpoint_p2p.listen(factory)
        _print("LISTEN P2P: {}".format(P2P_PORT))
    except CannotListenError:
        _print("ERROR: Port in use")
        sys.exit(1)

    # BootStrap Node
    _print ("Connecting to bootstrap node...")
    #if LOCALHOST != '127.0.0.2':
    if BOOTSTRAP_NODE != my_ip():
        point = TCP4ClientEndpoint(reactor, BOOTSTRAP_NODE, P2P_PORT)
        #point = TCP4ClientEndpoint(reactor, BOOTSTRAP_NODE, P2P_PORT, bindAddress=(LOCALHOST, 0))
        d = point.connect(factory)
        d.addCallback(bootstrapProtocol)
        d.addErrback(printError)

    reactor.run()
