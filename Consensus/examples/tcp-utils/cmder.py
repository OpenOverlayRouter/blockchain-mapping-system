#!/usr/bin/env python2.7

import zmq
import time
import argparse

def usage():
    print("You have the following commands available:")
    print("\tsetup/s \t Nodes will attempt to perform a DKG")
    print("\tconsensus/c \t Nodes will atempt to reach consensus")
    print("\thelp/h \t This message will be displayed")

def main(port):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://localhost:%s" % port)

        while True:
            cmd = raw_input("\nInput a command: ")
            if cmd == "help" or cmd == "h":
                usage()
            elif cmd == "setup" or cmd == "s":
                socket.send("setup")
                print("Initializing DKG...")
            elif cmd == "consensus" or cmd == "c":
                socket.send("consensus")
            else:
                print("Unknown command %s" % cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Publish broker socket", required=True, type=int)
    args = parser.parse_args()
    print("Launched commander on port %d" % args.p)
    usage();
    main(args.p)
