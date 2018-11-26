import os, sys, subprocess

EXE='utils/bls.exe'

class Bls():

    def __init__(self):
        self._isInit = False

    def initialize(self):
        if not self._isInit:
            self._isInit = True 
            subprocess.check_call([EXE, "init"])

    def sign(self, m, i=0):
        subprocess.check_call([EXE, "sign", "-m", m, "-id", str(i)])

    def verify(self, m, i=0):
        subprocess.check_call([EXE, "verify", "-m", m, "-id", str(i)])

    def share(self, n, k):
        subprocess.check_call([EXE, "share", "-n", str(n), "-k", str(k)])

    def recover(self, ids):
        cmd = [EXE, "recover", "-ids"]
        for i in ids:
                cmd.append(str(i))
        subprocess.check_call(cmd)

#def main():
#	m = "hello bls threshold signature"
#	n = 10
#	ids = [1, 5, 3, 7]
#	k = len(ids)
#	init()
#	sign(m)
#	verify(m)
#	share(n, k)
#	for i in ids:
#		sign(m, i)
#		verify(m, i)
#	subprocess.check_call(["rm", "sample/sign.txt"])
#	recover(ids)
#	verify(m)

#if __name__ == '__main__':
#    main()
