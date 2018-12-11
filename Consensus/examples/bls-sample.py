#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls


def main():

    myId = 1234
    m = "hello bls threshold signature"
    ids = [ 1, 5, 3]
    k = 2

    sk, pk = bls.genKeys()
    if not sk:
        print("Error initializing bls")
        return

    sm = bls.sign(m, sk)

    if not bls.verify(m, sm, pk):
        print("Error verifying initial message")
        return

    shares = bls.share(sk, k, ids)

    sigs = []
    for share in shares:
        aux = bls.sign(m, share["sk"])
        if not bls.verify(m, aux, share["pk"]):
            print("Error verifying message from id " + str(share["id"]))
            return

        sigs.append(aux)

    s = bls.recover(ids, sigs)
    if not bls.verify(m, s, pk):
        print("Recover failed")
        return

    print("Recover is OK")


if __name__ == "__main__":
    main()
