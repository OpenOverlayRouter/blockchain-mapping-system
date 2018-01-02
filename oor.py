import socket
import struct
from netaddr import IPAddress
import errno
import sys
from time import sleep
import fcntl
import os
import logger
import logging.config


HOST = ''
REC_PORT = 16001
SND_PORT = 16002

oorLog = logging.getLogger('OOR')


class Oor:

    def __init__(self):
        self.rec_socket, self.snd_socket = self.open_sockets()
        #self.logger = logging.getLogger('OOR')
        #self.logger = oorLog
        fcntl.fcntl(self.rec_socket, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.snd_socket, fcntl.F_SETFL, os.O_NONBLOCK)

    def open_sockets(self):
        try:
            rec_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            snd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            oorLog.info("Socket created.")
        except socket.error, msg:
            oorLog.exception('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1] + '.')
            sys.exit(1)
        # Bind socket to local host and port
        try:
            rec_socket.bind((HOST, REC_PORT))
        except socket.error:
            oorLog.exception("Bind failed.")
            sys.exit(1)

        oorLog.info('Socket bind complete in ports ' + str(REC_PORT) + ' and ' + str(SND_PORT))

        return rec_socket, snd_socket

    # reads the fields nonce, AFI and the IP from the socket
    def read_socket(self):
        try:
            res = self.rec_socket.recv(26)
            nonce = (struct.pack('>I', (int(struct.unpack("I", res[0:4])[0]))) + struct.pack('>I',(int(struct.unpack("I", res[4:8])[0])))).encode('HEX')
            nonce = int(nonce,16)
            afi = int(struct.unpack("H", res[8:10])[0])
            address = ''
            if (afi == 1):
                address = str(IPAddress(int(res[10:14].encode('HEX'),16)))

            elif (afi == 2):
                address = str(IPAddress(int(res[10:26].encode('HEX'),16)))
            else:
                raise Exception('Incorrect AFI read from socket.')
            return nonce, afi, address

        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                sleep(1)
                oorLog.info("No data available.")
                return None,None,None
            else:
                # a "real" error occurred
                oorLog.exception(e)

    def write_socket(self, res):
        self.snd_socket.sendto(res, (HOST, SND_PORT))

    def get_query(self):
        nonce, afi, address = self.read_socket()
        return nonce, afi, address
        """
        if(nonce is not None and afi is not None and address is not None):
            
            try:
                res = chain.query_eid(address, nonce)
            except Exception as e:
                print e
            
            locator = LocatorRecord(priority=0, weight=0, mpriority=0, mweight=0, unusedflags=0, LpR=0,
                                    locator=IPNetwork('192.168.0.1'))
            locators = []
            locators.append(locator)
            reply = MapReplyRecord(eid_prefix=IPNetwork('192.168.1.0/24'), locator_records=locators)
            reply = MapServers(info = [IPNetwork("192.168.1.42/32"),IPNetwork("192.168.0.2/32"),IPNetwork("192.168.0.3/32")])
            r = Response(nonce=nonce, info=reply)
            print(r.to_bytes().encode('HEX'))
            write_socket(r.to_bytes(), snd_socket)
            """

    def send(self, info):
        self.write_socket(info)
