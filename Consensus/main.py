#!/usr/bin/env python2.7

import libs.bls_wrapper as blslib


def main():

    myId = 1234
    m = "hello bls threshold signature"
    ids = [ 1, 5, 3]
    k = 2

    bls = blslib.Bls()
    if not bls.initialize():
        print("Error initializing bls")
        return

    sm = bls.sign(m)

    if not bls.verify(m, sm):
        print("Error verifying initial message")
        return

    shares = bls.share(k, ids)

    sigs = []
    for share in shares:
        aux = blslib.sign(m, share["sk"])
        if not blslib.verify(m, aux, share["pk"]):
            print("Error verifying message from id " + str(share["id"]))
            return

        sigs.append(aux)

    s = blslib.recover(ids, sigs)
    if not bls.verify(m, s):
        print("Recover failed")
        return

    print("Recover is OK")


if __name__ == "__main__":
    main()
