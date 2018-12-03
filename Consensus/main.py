#!/usr/bin/env python2.7

from libs.bls_wrapper import Bls


def main():

    m = "hello bls threshold signature"
    ids = [ 1, 5, 3]
    k = 2

    bls = Bls()
    bls.initialize()
    _, sm = bls.sign(m)
    
    if not bls.verify(m, sm):
        print("Error verifying initial message")
        return

    _, shares = bls.share(k, ids)
    
    sigs = []
    for share in shares:
        _, aux = bls.sign(m, share["sk"])
        if not bls.verify(m, aux, share["pk"]):
            print("Error verifying message from id " + str(share["id"]))
            return

        sigs.append(aux)
    
    _, s = bls.recover(ids, sigs)
    if not bls.verify(m, s):
        print("Recover failed")
        return

    print("Recover is OK")


if __name__ == "__main__":
    main()
