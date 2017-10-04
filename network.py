import sys
from datetime import datetime
from os import urandom

from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.internet.address import UNIXAddress
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import Protocol, Factory
from twisted.python.filepath import FilePath
from twisted.python import log

BOOTSTRAP_NODES = ["localhost:5010",
                   "localhost:5011"]

#log.startLogging(sys.stdout)

def _print(msg):
    print("[{}] {}".format(str(datetime.now()), msg))


class myProtocol(Protocol):
    def __init__(self, factory, addr):
        self.factory = factory
        self.address = addr
        self.nodeid = None
        self.state = 'NODEID'

    def connectionMade(self):
        self.transport.write(self.factory.nodeid.encode('utf-8'))
    
    def connectionLost(self, reason):
        if self.nodeid is not None:
            _print("Connection Lost: {}".format(self.address))
            del self.factory.peers[self.nodeid]
        else:
            _print("Connection Error: {}".format(self.address))

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            if self.state == 'NODEID':
                if self.factory.peers.get(line) is None:
                    self.nodeid = line
                    self.factory.peers[self.nodeid] = self
                    _print("New Peer: {} {}".format(line, self.address))
                    self.state = None
                else:
                    self.transport.loseConnection()
            elif self.state == 'UNIX':
                self.factory.unix_sock.sendMsg(line)
            else:
                print (line)

    def sendMsg(self, msg):
        self.transport.write(msg + b'\r\n')
        self.state = 'UNIX'


class UnixProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        if self.factory.unix_sock is None:
            self.factory.unix_sock = self
            _print("Unix Connection")
        else:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        pass

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
        self.nodeid = urandom(256//8).hex()
        print ("NodeID: {}".format(self.nodeid))

    def startFactory(self):
        self.peers = {}
        self.unix_sock = None
    
    def stopFactory(self):
        pass
    
    def buildProtocol(self, addr):
        if type(addr) == UNIXAddress:
            return UnixProtocol(self)
        return myProtocol(self, addr)


if __name__ == '__main__':
    port = 5005
    path = FilePath("block.sock")
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    elif len(sys.argv) > 2:
        port = int(sys)
        path = FilePath(sys.argv[2])

    try:
        endpoint = TCP4ServerEndpoint(reactor, port)
        factory = myFactory()
        endpoint.listen(factory)
        _print("LISTEN: {}".format(port))
        unixpoint = reactor.listenUNIX(path.path, factory)
    except CannotListenError:
        _print("ERROR: Port in use")
        sys.exit(1)

    # TODO BootStrap

    reactor.run()
