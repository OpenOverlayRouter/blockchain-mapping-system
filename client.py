import socket
import struct


# this class must be used to send a message to the server
class Client():
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('localhost', 50000))

    # this function sends the message to the server in a format the server understands
    def send(self, message):
        msg = struct.pack('>I', len(message)) + message
        self.s.sendall(msg)
