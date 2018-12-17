#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls
import dkg as dkg
from random import randint
import argparse

def dkgSetup(ids, threshold):
    members = []
    for member in ids:
        secKey, _ = bls.genKeys(member)
        members.append({
            "originalId": member,
            "id": secKey,
            "receivedShares": [],
            "secretKeyShare": None
        })

    print("Beginning the secret instantation round...")
    print("\tUsing members: " + " ".join(map(str, ids)))
    print("\tUsing threshold of: " + str(threshold))

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

    print("-> Secret shares have been generated")

    groupsvVec = dkg.addVerificationVectors(vVecs)
    print("-> Verification vector computed")
    print("Resulting group public key is " + (groupsvVec[0]) + "\n")

    return members, groupsvVec

def dkgTest(msg, members, vVec, threshold):
    groupsPk = vVec[0]
    sigs = []
    signerIds = []

    print("Testing signature on message \"" + msg + "\"")

    while len(sigs) < threshold:
        i = randint(0, len(members)-1)
        if members[i]["id"] in signerIds:
            continue

        skShare = members[i]["secretKeyShare"]
        print("-> Member " + str(members[i]["originalId"]) + " signs with share: " + skShare)
        sig = bls.sign(msg, skShare)
        sigs.append(sig)
        signerIds.append(members[i]["id"])

    groupsSig = bls.recover(signerIds, sigs)
    print("Resulting sig: " + groupsSig)

    verified = bls.verify(msg, groupsSig, groupsPk)
    print(("\033[92m" if verified else "\033[91mNOT ") + "VERIFIED \033[0m\n")

    return groupsSig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="Ids of members of the dkg", nargs="*", default=[ 10314, 30911, 25411, 8608, 31524, 15441, 23399], type=int)
    parser.add_argument("-th", help="Threshold of the threshold signature that will be setup", nargs="?", type=int)
    parser.add_argument("-rr", help="Amount of times a dkg round will be repeated (for the same message)", nargs="?", default=2, type=int)
    parser.add_argument("-nr", help="Amount of rounds, where the message from the previous round will be signed", nargs="?", default=5, type=int)
    args = parser.parse_args()

    ids = args.m
    threshold = args.th if args.th else len(ids)/2 + len(ids)%2
    numRounds = args.nr
    roundRepeat = args.rr

    members, vVec = dkgSetup(ids, threshold)

    msg = "This is a dkg sample"
    for i in range(numRounds):
        print("ROUND " + str(i+1))
        print("----------------------------------------")
        roundMsg = msg
        for j in range(roundRepeat):
            msg = dkgTest(roundMsg, members, vVec, threshold)


if __name__ == "__main__":
    main()
