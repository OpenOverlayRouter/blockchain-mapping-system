# 58 character alphabet used
alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58encode(s):
    n = int(s,16)
    result = ''
    while n > 0:
        result = alphabet[n%58] + result
        n //= 58
    return result

def b58decode(s):
    result = 0
    for i in range(0, len(s)):
        result = result * 58 + alphabet.index(s[i])
    return '{:x}'.format(result).zfill(50)
