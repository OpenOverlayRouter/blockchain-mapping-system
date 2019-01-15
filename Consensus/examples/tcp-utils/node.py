#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
import libs.bls_wrapper as bls
import dkg as dkg
import zmq
import signal
import json
import argparse
import logger

signal.signal(signal.SIGINT, signal.SIG_DFL);

log = None
sk = None
groupPk = None
state = "ipchain"
sigs = None
sigIds = None
addrs = {}
brokerAddr = None


def init(oid, threshold, pport, sport):
    global log, sk, addrs, brokerAddr
    log = logger.setup_custom_logger(str(oid))
    members = {}
    oids = []

    for line in open("examples/tcp-utils/members.txt").readlines():
        lines = line.split(' ')
        id = int(lines[0])
        addr = lines[1].rstrip("\n")
        oids.append(id)
        if not brokerAddr:
            brokerAddr = addr
        addrs[id] = addr

    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect("tcp://%s:%s" % (brokerAddr, sport))
    sub.setsockopt(zmq.SUBSCRIBE, "")

    pub = ctx.socket(zmq.PUB)
    pub.connect("tcp://%s:%s" % (brokerAddr, pport))

    socket = ctx.socket(zmq.REP)
    socket.bind("tcp://*:%s" % oid)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    poller.register(sub, zmq.POLLIN)

    end = False

    log.info("%d: Started communications..." % oid)
    while not end:
        socks = dict(poller.poll())
        if sub in socks and socks[sub] == zmq.POLLIN:
            msg = sub.recv()
            type = msg.split("_", 1)[0]
            if type == "setup":
                setup(members, oid, oids, threshold)
            elif type == "consensus" and sk is not None:
                    pub.send(genNewSig(oid))
            elif type == "sig":
                handleSig(json.loads(msg.split("_", 1)[1]), threshold, members)

        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = json.loads(socket.recv())
            topic = msg["topic"]
            if topic == "contrib":
                receiveContribution(msg, members, oid)
                socket.send("OK")

def genNewSig(m_oid):
    global state, sk, sigs, sigIds
    sig = bls.sign(state, sk)
    sigs = []
    sigIds = []

    return ("sig_" + json.dumps({
            "oid": m_oid,
            "sig": sig
        }))

def handleSig(msg, threshold, members):
    global sigs, groupPk, state, sigIds

    if not groupPk:
        return

    sigs.append(msg["sig"]);
    sigIds.append(members[msg["oid"]]["id"]);

    log.info("Received secretShare %s" % msg["sig"])

    if (len(sigs) >= threshold):
        groupsSig = bls.recover(sigIds, sigs)

        if bls.verify(state, groupsSig, groupPk):
            state = groupsSig
            log.info("Verified sig %s. Updating state..." % groupsSig)

def receiveContribution(msg, members, m_oid):
    oid = msg["oid"]
    contrib = msg["contrib"]
    vVec = msg["vvec"]

    if dkg.verifyContributionShare(members[m_oid]["id"], contrib, vVec):
        members[oid]["receivedShare"] = contrib
        members[oid]["vvec"] = vVec
        log.info("Received valid share from member %s" % oid)
    else:
        log.info("Received invalid share from member %s" % oid)

    if allSharesReceived(members):
        global sk, groupPk
        sk = dkg.addContributionShares( [ member["receivedShare"] for _,member in members.iteritems() ])
        groupsvVec = dkg.addVerificationVectors( [ member["vvec"] for _,member in members.iteritems() ])
        groupPk = groupsvVec[0]
        log.info("DKG setup completed")
        log.info("Resulting group public key is " + groupPk + "\n")

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
                "vvec": vVec,
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
    global addrs
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://%s:%d" % (addrs[to], to))
    socket.send(json.dumps(data));
    return context, socket

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", help="Id of this node", required=True, type=int)
    parser.add_argument("-s", help="Subscribe broker socket", required=True, type=int)
    parser.add_argument("-p", help="Publish broker socket", required=True, type=int)
    parser.add_argument("-t", help="Threshold", required=True, type=int)
    args = parser.parse_args()
    init(args.id, args.t, args.p, args.s)
