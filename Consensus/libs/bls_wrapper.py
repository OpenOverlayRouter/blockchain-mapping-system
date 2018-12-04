import os, re, sys, subprocess

EXE='utils/bls.exe'

class Bls():

    def __init__(self):
        self._isInit = False

    def initialize(self, id):
        if not self._isInit:
            self._isInit = True
            try:
                out = subprocess.check_output([EXE, "init", "-id", str(id)])
            except subprocess.CalledProcessError:
                return False

            m = re.search(r"secKey: (.+)\npubKey: (.+)", out)

            if not m:
                return False

            self.secKey = m.group(1)
            self.pubKey = m.group(2)

        return True

    def sign(self, m):
        if not self._isInit:
            return False, ""
        
        return bls_sign(m, self.secKey)

    def verify(self, m, sm):
        if not self._isInit:
            return False
        
        return bls_verify(m, sm, self.pubKey)

    def share(self, k, ids):
        result = []
        cmd = [EXE, "share", "-sk", self.secKey, "-k", str(k), "-ids"]
        for i in ids:
            cmd.append(str(i))

        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            return False, []

        matches = re.findall( r"share-0x.+: sk=(.+) pk=(.+)", out)
        if len(matches) != len(ids):
            return False, []

        for index, id in enumerate(ids):
            result.append({
                "id": id,
                "sk": matches[index][0],
                "pk": matches[index][1]
            })

        return True, result

    def recover(self, ids, sigs):
        cmd = [EXE, "recover", "-ids"]
        for i in ids:
            cmd.append(str(i))

        cmd.append("-sigs")
        for sig in sigs:
            cmd.append(str(sig))

        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            return False, ""

        m = re.search(r"recovered: (.+)", out)
        return True, m.group(1)


def bls_getPublicKey(sk):
    cmd = [EXE, "getpk", "-sk", sk]
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return ""

    return re.match(r"pk: (.+)", out).group(1)

def bls_sign(m, sk):
    try:
        out = subprocess.check_output([EXE, "sign", "-m", m, "-sk", str(sk)])
    except subprocess.CalledProcessError:
        return False, ""

    m = re.search(r"sMsg: (.+)", out)
    return True, m.group(1)


def bls_verify(m, sm, pk):
    try:
        subprocess.check_output([EXE, "verify", "-pk", pk, "-m", m, "-sm", sm])
    except subprocess.CalledProcessError:
        return False

    return True
