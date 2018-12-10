import os, re, sys, subprocess

EXE='utils/bls.exe'

class Bls():

    def __init__(self):
        self._isInit = False

    def initialize(self, id=None):
        if not self._isInit:
            try:
                cmd = [EXE, "init"]
                if id is not None:
                    cmd.extend([ "-id", str(id) ]);

                out = subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                return False

            m = re.search(r"secKey: (.+)\npubKey: (.+)", out)

            if not m:
                return False

            self.secKey = m.group(1)
            self.pubKey = m.group(2)

        self._isInit = True
        return True

    def sign(self, m):
        if not self._isInit:
            return ""

        return sign(m, self.secKey)

    def verify(self, m, sm):
        if not self._isInit:
            return False

        return verify(m, sm, self.pubKey)

    def share(self, k, ids):
        result = []
        cmd = [EXE, "share", "-sk", self.secKey, "-k", str(k), "-ids"]
        for i in ids:
            cmd.append(str(i))

        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            return []

        matches = re.findall( r"share-0x.+: sk=(.+) pk=(.+)", out)
        if len(matches) != len(ids):
            return []

        for index, id in enumerate(ids):
            result.append({
                "id": id,
                "sk": matches[index][0],
                "pk": matches[index][1]
            })

        return result

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
            return ""

        m = re.search(r"recovered: (.+)", out)
        if not m:
            return ""

        return m.group(1)

def sign(m, sk):
    try:
        out = subprocess.check_output([EXE, "sign", "-m", m, "-sk", str(sk)])
    except subprocess.CalledProcessError:
        return ""

    m = re.search(r"sMsg: (.+)", out)
    if not m:
        return ""
    
    return m.group(1)


def verify(m, sm, pk):
    try:
        subprocess.check_output([EXE, "verify", "-pk", pk, "-m", m, "-sm", sm])
    except subprocess.CalledProcessError:
        return False

    return True

def getPublicKey(sk):
    cmd = [EXE, "getpk", "-sk", sk]
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return ""

    m = re.match(r"pk: (.+)", out)
    if not m:
        return ""

    return m.group(1)

def secretKeyShare(id, sKeys):
    cmd = [EXE, "secshare", "-sid", str(id), "-keys"]
    for sk in sKeys:
        cmd.append(sk)

    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return ""

    m = re.match(r"sk: (.+)", out)
    if not m:
        return ""

    return m.group(1)

def publicKeyShare(id, pKeys):
    cmd = [EXE, "pubshare", "-sid", str(id), "-keys"]
    for pk in pKeys:
        cmd.append(pk)

    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return ""

    m = re.match(r"pk: (.+)", out)
    if not m:
        return ""

    return m.group(1)

def publicKeyIsEqual(pk1, pk2):
    try:
        subprocess.check_call([EXE, "eqpks", "-keys", str(pk1), str(pk2)])
    except subprocess.CalledProcessError:
        return False

    return True

def secretKeyAdd(sk1, sk2):
    try:
        out = subprocess.check_output([EXE, "addsks", "-keys", str(sk1), str(sk2)])
    except subprocess.CalledProcessError:
        return ""

    m = re.match(r"sk: (.+)", out)
    if not m:
        return ""

    return m.group(1)