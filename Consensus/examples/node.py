#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls
import dkg as dkg
import zmq
import signal
import json
import argparse
from threading import Thread
import Queue
import logger

signal.signal(signal.SIGINT, signal.SIG_DFL);

def init(oid, oids, port):
    global log
    log = logger.setup_custom_logger(str(oid))
    threshold = int(len(oids)/2 + len(oids)%2)
    members = {}

    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect("tcp://localhost:%s" % port)
    sub.setsockopt(zmq.SUBSCRIBE, "")

    socket = ctx.socket(zmq.REP)
    socket.bind("tcp://*:%s" % oid)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    poller.register(sub, zmq.POLLIN)

    contribQueue = Queue.Queue()
    end = False

    thread = Thread(target = handleContribs, args = (contribQueue, end, members, oid))
    thread.start()

    log.info("%d: Started communications..." % oid)
    while not end:
        socks = dict(poller.poll())
        if sub in socks and socks[sub] == zmq.POLLIN:
            if sub.recv() == "setup":
                setup(members, oid, oids, threshold)
        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = json.loads(socket.recv())
            topic = msg["topic"]
            if topic == "contrib":
                contribQueue.put(msg)
                socket.send("OK")
            elif topic == "vvec":
                vvec = []
                if oid in members:
                    vvec = members[oid]["vvec"]
                socket.send(json.dumps(vvec))

    thread.join()

def handleContribs(contribQueue, end, members, oid):
    while not end:
        receiveContribution(contribQueue.get(), members, oid)


def receiveContribution(msg, members, m_oid):
    oid = msg["oid"]
    contrib = msg["contrib"]

    vVec = getVerificationVector(m_oid, oid)

    if dkg.verifyContributionShare(members[m_oid]["id"], contrib, vVec):
        members[oid]["receivedShare"] = contrib
        members[oid]["vvec"] = vVec
        log.info("Received valid share from member %s" % oid)
    else:
        log.info("Received invalid share from member %s" % oid)

    if allSharesReceived(members):
        sk = dkg.addContributionShares( [ member["receivedShare"] for _,member in members.iteritems() ])
        groupsvVec = dkg.addVerificationVectors( [ member["vvec"] for _,member in members.iteritems() ])
        log.info("DKG setup completed")
        log.info("Resulting group public key is " + (groupsvVec[0]) + "\n")

def setup(members, m_oid, oids, threshold):
    members.clear()
    for oid in oids:
        secKey, _ = bls.genKeys(oid)
        members[oid] = {
            "id": secKey,
            "receivedShare": None,
            "vvec": None
        }

    vVec, skContrib = dkg.generateContribution(threshold,
                                               [ member["id"] for _,member in members.iteritems() ] )

    i = 0
    for oid, member in members.iteritems():
        if oid == m_oid:
            members[m_oid]["vvec"] = vVec
            members[m_oid]["receivedShare"] = skContrib[i]
        else:
            sendMsg(oid, {
                "oid": m_oid,
                "topic": "contrib",
                "contrib": skContrib[i]
            })
        i += 1

def getVerificationVector(m_oid, oid):
    ctx, socket = sendMsg(oid, {
        "topic": "vvec",
        "oid": m_oid
    })

    return json.loads(socket.recv())

def allSharesReceived(members):
    for _,member in members.iteritems():
        if not member["receivedShare"]:
            return False

    return True

def sendMsg(to, data):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:%d" % to)
    socket.send(json.dumps(data));
    return context, socket

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", help="Id of this node", required=True, type=int)
    parser.add_argument("-ids", help="Ids of all the nodes", nargs="*", required=True, type=int)
    parser.add_argument("-p", help="Port of socket that sends setup time", required=True, type=int)
    args = parser.parse_args()
    init(args.id, args.ids, args.p)
