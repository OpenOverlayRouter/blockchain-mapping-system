import os, re, sys, subprocess

EXE='utils/bls.exe'

def genKeys(id=None):
    cmd = [EXE, "init"]
    if id is not None:
        cmd.extend([ "-id", str(id) ]);
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return "", ""

    m = re.search(r"secKey: (.+)\npubKey: (.+)", out)

    if not m:
        return "", ""

    return m.group(1), m.group(2)

def share(sk, k, ids):
    result = []
    cmd = [EXE, "share", "-sk", sk, "-k", str(k), "-ids"]
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
    cmd = [EXE, "verify", "-pk", pk, "-m", m, "-sm", sm]

    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return False

    return True

def recover(ids, sigs):
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

def publicKeyAdd(pk1, pk2):
    try:
        out = subprocess.check_output([EXE, "addpks", "-keys", str(pk1), str(pk2)])
    except subprocess.CalledProcessError:
        return ""

    m = re.match(r"pk: (.+)", out)
    if not m:
        return ""

    return m.group(1)
