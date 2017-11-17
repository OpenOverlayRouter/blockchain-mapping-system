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

GLOBAL_PORT = 5005
QUERY_PORT = 5006
P2P_PORT = 5007
HOST = '127.0.0.1'

BOOTSTRAP_NODES = ["127.0.0.2"]

PING_TIME = 20

#log.startLogging(sys.stdout)

def _print(msg):
    print("[{}] {}".format(str(datetime.now()), msg))


class p2pProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        #self.address = addr
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
                    if data["msgtype"] == "pong":
                        #print self.transport.getPeer().host
                        self.pong = True
                    if data["msgtype"] == "get_peers":
                        kwargs = {"peers": self.factory.peers_ip}
                        self.sendMsg("set_peers", kwargs)
                    if data["msgtype"] == "set_peers":
                        print data.get("peers")
                        peers = data.get("peers")
                        for key in peers:
                            exists = self.factory.peers_ip.get(key)
                            if exists is None and key != self.factory.nodeid:
                                p = int(HOST.split('.')[-1]*2+peers.get(key).split('.')[-1]*2)
                                #print key, peers.get(key), P2P_PORT, p
                                point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT, bindAddress=(HOST, p))
                                connectProtocol(point, p2pProtocol(self.factory))
                                #point = TCP4ClientEndpoint(reactor, peers.get(key), P2P_PORT)
                                
                except Exception as exception:
                    print "except", exception.__class__.__name__, exception
                    self.transport.loseConnection()
                #else:
                    #print (line)

    def sendMsg(self, msgtype, msg):
        msg = messages.make_envelope(msgtype, **msg)
        self.transport.write(msg)
    
    '''def sendMsg(self, msg):
        self.transport.write(msg + b'\r\n')
        self.state = 'LOCAL'''
    
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
        self.transport.write(messages.get_peers())


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
            for nodeid, address in self.factory.peers.items():
                address.sendMsg(line)

    def sendMsg(self, msg):
        self.transport.write(msg + b'\r\n')


class myFactory(Factory):
    def __init__(self):
        self.nodeid = urandom(128//8).encode('hex')
        print ("NodeID: {}".format(self.nodeid))

    def startFactory(self):
        self.peers = {}
        self.peers_ip = {}
        self.local = None
    
    def stopFactory(self):
        pass
    
    def buildProtocol(self, addr):
        # TODO check port
        #print("hello", addr)
        '''if addr.host == "127.0.0.1":
            return localProtocol(self)
        return p2pProtocol(self, addr)'''
        if addr.port == QUERY_PORT:
            return localProtocol(self)
        return p2pProtocol(self)



def printError(failure):
    print (failure.getErrorMessage())


def bootstrapProtocol(p):
    print "BOOTSTRAPING"
    p.sendGetPeers()


if __name__ == '__main__':
    '''if len(sys.argv) > 1:
        print ("Error: too many arguments")
        sys.exit(1)'''
    if len(sys.argv) == 2:
        HOST = sys.argv[1]
    elif len(sys.argv) > 2:
        print ("Error: too many arguments")
        sys.exit(1)

    try:
        factory = myFactory()
        #endpoint_local = TCP4ServerEndpoint(reactor, GLOBAL_PORT)
        #endpoint_local.listen(factory)
        #_print("LISTEN: {}".format(GLOBAL_PORT))
        endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT, interface=HOST)
        #endpoint_p2p = TCP4ServerEndpoint(reactor, P2P_PORT)
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
            #point = TCP4ClientEndpoint(reactor, host, P2P_PORT)
            p = int(HOST.split('.')[-1])*1000
            point = TCP4ClientEndpoint(reactor, host, P2P_PORT, bindAddress=(HOST, p))
            d = point.connect(factory)
            d.addCallback(bootstrapProtocol)
            d.addErrback(printError)

    reactor.run()
