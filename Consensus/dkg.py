#!/usr/bin/env python2.7

from libs.bls_wrapper import *

def generateContribution(bls, threshold, ids):
    b, shares = bls.share(threshold, ids)
    return [ share["pk"] for share in shares ], [ share["sk"] for share in shares ]

def main():

    members = []
    threshold = 4
    for member in [ 10314, 30911, 25411, 8608, 31524, 15441, 23399 ]:
        bls = Bls()
        bls.initialize(member)
        members.append({
            "id": bls.secKey,
            "bls": bls,
            "receivedShares": []
        })

    print("Beginning the secret instantation round...")

    vVecs = []
    for current in members:
        vVec, skContribs = generateContribution(current["bls"], threshold, [ m["id"] for m in members ] )
        vVecs.append(vVec)

        for i, contrib in enumerate(skContribs):
            member = members[i]
            pk = bls_getPublicKey(contrib)
            b = True
            if not b:
                print("Invalid share!")
                return
            
            member["receivedShares"].append(contrib)
            


if __name__ == "__main__":
    main()
