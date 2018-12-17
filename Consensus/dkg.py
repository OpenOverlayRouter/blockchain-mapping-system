#!/usr/bin/env python2.7

import libs.bls_wrapper as bls

def generateContribution(threshold, ids):
    vVec = []
    sVec = []
    skContrib = []

    for _ in range(threshold):
        secKey, pubKey = bls.genKeys()
        sVec.append(secKey)
        vVec.append(pubKey)

    for id in ids:
        sk = bls.secretKeyShare(id, sVec)
        skContrib.append(sk)

    return vVec, skContrib

def verifyContributionShare(id, contribution, vVec):
    pk1 = bls.publicKeyShare(id, vVec)
    pk2 = bls.getPublicKey(contribution)

    return bls.publicKeyIsEqual(pk1, pk2)

def addContributionShares(secretKeyShares):
    first = secretKeyShares.pop()
    for sk in secretKeyShares:
        first = bls.secretKeyAdd(first, sk)

    return first

def addVerificationVectors(vVecs):
    groupsvVec = [None] * len(vVecs[0])
    for vVec in vVecs:
        for i, pk2 in enumerate(vVec):
            pk1 = groupsvVec[i]
            if not pk1:
                groupsvVec[i] = pk2
            else:
                groupsvVec[i] = bls.publicKeyAdd(pk1, pk2)

    return groupsvVec
