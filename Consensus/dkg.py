#!/usr/bin/env python2.7

import libs.bls_wrapper as blslib

def generateContribution(threshold, ids):
    vVec = []
    sVec = []
    skContrib = []

    for _ in range(threshold):
        bls = blslib.Bls()
        bls.initialize()
        sVec.append(bls.secKey)
        vVec.append(bls.pubKey)
    
    for id in ids:
        sk = blslib.secretKeyShare(id, sVec)
        skContrib.append(sk)
    
    return vVec, skContrib

def verifyContributionShare(id, contribution, vVec):
    pk1 = blslib.publicKeyShare(id, vVec)
    pk2 = blslib.getPublicKey(contribution)

    return blslib.publicKeyIsEqual(pk1, pk2)

def addContributionShares(secretKeyShares):
    first = secretKeyShares.pop()
    for sk in secretKeyShares:
        first = blslib.secretKeyAdd(first, sk)
    
    return first

def addVerificationVectors(vVecs):
    groupsvVec = [None] * len(vVecs[0])
    for vVec in vVecs:
        for i, pk2 in enumerate(vVec):
            pk1 = groupsvVec[i]
            if not pk1:
                groupsvVec[i] = pk2
            else:
                groupsvVec[i] = blslib.publicKeyAdd(pk1, pk2)

    return groupsvVec

def main():
    members = []
    threshold = 4
    for member in [ 10314, 30911, 25411, 8608, 31524, 15441, 23399 ]:
        bls = blslib.Bls()
        bls.initialize(member)
        members.append({
            "id": bls.secKey,
            "bls": bls,
            "receivedShares": []
        })

    print("Beginning the secret instantation round...")

    vVecs = []
    for _ in members:
        verificationVector, secretKeyContribution = generateContribution(threshold, [ m["id"] for m in members ] )
        vVecs.append(verificationVector)

        for i, contrib in enumerate(secretKeyContribution):
            member = members[i]
            b = verifyContributionShare(member["id"], contrib, verificationVector)
            if not b:
                print("Invalid share!")
                return
            
            member["receivedShares"].append(contrib)

    for member in members:
        sk = addContributionShares(member["receivedShares"])
        member["secretKeyShare"] = sk

    print("Secret shares have been generated")

    groupsvVec = addVerificationVectors(vVecs)
    print("Verification vector computed")

    groupsPk = groupsvVec[0]


if __name__ == "__main__":
    main()
