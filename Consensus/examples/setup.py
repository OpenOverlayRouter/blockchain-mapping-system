#!/usr/bin/env python2.7

import zmq
import time
import argparse

def main(port):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:%s" % port)
        while True:
            socket.send("setup")
            time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Port of the socket that sends setup", required=True, type=int)
    args = parser.parse_args()
    main(args.p)
