#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls
import dkg as dkg
from random import randint

def dkgSetup(ids, threshold):
    members = []
    for member in ids:
        secKey, _ = bls.genKeys(member)
        members.append({
            "id": secKey,
            "receivedShares": []
        })

    print("Beginning the secret instantation round...")

    vVecs = []
    for _ in members:
        verificationVector, secretKeyContribution = dkg.generateContribution(threshold, [ m["id"] for m in members ] )
        vVecs.append(verificationVector)

        for i, contrib in enumerate(secretKeyContribution):
            member = members[i]
            b = dkg.verifyContributionShare(member["id"], contrib, verificationVector)
            if not b:
                print("Invalid share!")
                return

            member["receivedShares"].append(contrib)

    for member in members:
        sk = dkg.addContributionShares(member["receivedShares"])
        member["secretKeyShare"] = sk

    print("Secret shares have been generated")

    groupsvVec = dkg.addVerificationVectors(vVecs)
    print("Verification vector computed")
    print("Secret instantation round completed with groupPk: " + (groupsvVec[0]))

    return members, groupsvVec

def dkgTest(members, vVec, threshold):
    groupsPk = vVec[0]
    msg = "Hello world"
    sigs = []
    signerIds = []

    print("Testing signature")

    while len(sigs) < threshold:
        i = randint(0, len(members)-1)
        if members[i]["id"] in signerIds:
            continue

        skShare = members[i]["secretKeyShare"]
        print(str(i) + " is signing the message with share: " + skShare)
        sig = bls.sign(msg, skShare)
        sigs.append(sig)
        signerIds.append(members[i]["id"])

    groupsSig = bls.recover(signerIds, sigs)
    print("sigtest result: " + groupsSig)

    verified = bls.verify(msg, groupsSig, groupsPk)
    if verified:
        print("VERIFIED!")
    else:
        print("NOT VERIFIED!")

def main():
    ids = [ 10314, 30911, 25411, 8608, 31524, 15441, 23399 ]
    threshold = 4
    members, vVec = dkgSetup(ids, threshold)
    numTests = 5
    for i in range(numTests):
        dkgTest(members, vVec, threshold)


if __name__ == "__main__":
    main()
