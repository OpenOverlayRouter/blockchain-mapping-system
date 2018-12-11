#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls
import dkg as dkg
import requests

from flask import Flask, jsonify
app = Flask(__name__)


m_id = None
m_ids = [line.rstrip('\n') for line in open("examples/members.txt")]
m_threshold = int(len(m_ids)/2 + len(m_ids)%2)
m_members = None

@app.route("/contrib/", methods=["POST"])
def receiveContribution():
    content = request.json
    id = content["id"]
    contrib = content["contrib"]

    vVec = getVerificationVector(id)

    if dkg.verifyContributionShare(id, contrib, vVec):
        m_members[id]["receivedShare"] = contrib
        m_members[id]["vvec"] = vVec
        print("Received valid share from member " + id)
    else:
        print("Received invalid share from member " + id)

    if allSharesReceived():
        sk = dkg.addContributionShares(member["receivedShares"])
        groupsvVec = dkg.addVerificationVectors(vVecs)
        print("DKG setup completed")
        print("Resulting group public key is " + (groupsvVec[0]) + "\n")

@app.route("/vvec/", methods=["GET"])
def sendVerificationVector():
    return jsonify(vvec=m_vVec)

@app.route("/setup")
def setup():
    m_members = {}
    for id in m_ids:
        secKey, _ = bls.genKeys(id)
        m_members[id] = {
            "id": secKey,
            "receivedShare": None,
            "vvec": None
        }

    vVec, skContrib = dkg.generateContribution(m_threshold, [ member["id"] for member in m_state ] )
    for i, contrib in enumerate(skContrib):
        url = getUrl(m_members[i])+"/contrib"
        requests.post(url, json=jsonify(id=m_id, contrib=contrib))

    m_members[m_id]["vvec"] = vVec

def getUrl(member):
    return "http://127.0.0.1:"+member

def getVerificationVector(member):
    url = getUrl(m_members[i])+"/vvec"
    content = requests.get(url).json()

    return content["vvec"]

def allSharesReceived():
    for member in m_members:
        if not member["receivedShare"]:
            return False

    return True
