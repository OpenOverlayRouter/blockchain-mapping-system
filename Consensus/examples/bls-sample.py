#!/usr/bin/env python2.7

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import libs.bls_wrapper as bls


def main():

    m = "hello bls threshold signature"
    ids = [ '0x0be38dcb62b45984cf4ffdeabb68de5e78151304', '0x0eccc8117f80534a9001874c256c11573c9a31bc', '0x219fb4dc55bf5f4e3144ea9e8b4fc0835175fabe', '0x243278af80ab7e23e559e3b6c4f4d494bfe624a9']
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
