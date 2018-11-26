#!/usr/bin/env python2.7

from libs.bls_wrapper import Bls


def main():
    bls = Bls()
    bls.initialize()


#       m = "hello bls threshold signature"
#       n = 10
#       ids = [1, 5, 3, 7]
#       k = len(ids)
#       init()
#       sign(m)
#       verify(m)
#       share(n, k)
#       for i in ids:
#               sign(m, i)
#               verify(m, i)
#       subprocess.check_call(["rm", "sample/sign.txt"])
#       recover(ids)
#       verify(m)



if __name__ == "__main__":
    main()
