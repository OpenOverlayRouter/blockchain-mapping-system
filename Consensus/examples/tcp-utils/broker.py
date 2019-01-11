#!/usr/bin/env python2.7

import zmq
import time
import argparse

def main(pport, sport):
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        publisher.bind("tcp://*:%s" % sport)

        subscriber = context.socket(zmq.SUB)
        subscriber.bind("tcp://*:%s" % pport)
        subscriber.setsockopt(zmq.SUBSCRIBE, "")

        zmq.device(zmq.FORWARDER, subscriber, publisher)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Broker publish socket", required=True, type=int)
    parser.add_argument("-s", help="Broker subscribe socket", required=True, type=int)
    args = parser.parse_args()
    print("Launched broker with publish port %d and subscriber port %d" % (args.p, args.s))
    main(args.p, args.s)
