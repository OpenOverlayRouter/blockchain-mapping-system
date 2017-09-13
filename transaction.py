import cryptography as cr

__version__ = '1'   # Must have integer representation

def length_to_bytes(n):
    r = b''
    if n < 253:
        length = 1
    elif n <= 0xFFFF:
        length = 2
        r += bytes.fromhex('fd') 
    elif n <= 0xFFFFFFFF:
        length = 4
        r += bytes.fromhex('fe')
    else:
        length = 8
        r += bytes.fromhex('ff')
    r += n.to_bytes(length=length, byteorder='little')
    return r


def make_output(output):
    script, ips = output
    return bytes.fromhex(script)


def get_script(input):
    return bytes.fromhex('0000000000000000')


def make_transaction(privkeys, inputs, outputs, locktime):
    tx = b''
    tx += int(__version__).to_bytes(length=4, byteorder='little')   # 4 bytes

    tx += length_to_bytes(len(inputs)) # 1+ bytes

    tx_out = b''
    tx_out += length_to_bytes(len(outputs)) # +1 bytes
    tx_out += b''.join(map(make_output, outputs))
    
    prev_scripts = list(map(get_script, inputs))

    pub_keys = list(map(cr.privkey_to_pubkey, privkeys))

    script_sigs = []
    for i, input in enumerate(inputs):
        tx_aux = tx
        for j in range(i):
            tx_aux += bytes.fromhex(input[0])
            tx_aux += int(input[1]).to_bytes(length=4, byteorder='little')
            tx_aux += bytes.fromhex('00')
        tx_aux += bytes.fromhex(input[0])
        tx_aux += int(input[1]).to_bytes(length=4, byteorder='little')
        tx_aux += prev_scripts[i]
        tx_aux += tx_out
        sig = cr.generate_signature(privkeys[i], tx_aux)
        script_sig = len(sig) + sig + len(pub_keys[i]) + pub_keys[i]
        script_sigs.append(bytes.fromhex(len(script_sig) + script_sig))

    tx_in = b''
    for i, input in enumerate(inputs):
        tx_in += bytes.fromhex(input[0])
        tx_in += int(input[1]).to_bytes(length=4, byteorder='little')
        tx_in += prev_scripts[i]
        tx_in += script_sigs[i]

    tx += tx_in + tx_out + bytes.fromhex(locktime)
    return tx


def main():
    # TESTS
    privkeys = ['2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c',
               '1cb99b78710454890b32a6207e72b335d55e8222e8ec6af5c416f5daf601bc44',
               '84cd947d91cf4b13b573988f829b2573ff4a15eebb1a39c4288ec45ef7dc0b10']
    
    inputs = [('3110b2c2810b6d3a2c558ba62cc305a4b75ddbda6b0204f44d5cb80564c63852', '0'),
              ('d1bd200ecf87320b3f5bb465c7ade141067bc9f1e0623726e1f9a282bb3f3b91', '3'),
              ('3b04a3c1a4155f757374b29786f3f7c43273f7638f5d94b8c38fbd3e4888fbb7', '1')]

    outputs = [('227be909766b35e4d9e0252de237d89ce13172df', '0.0.0.0'),
               ('5989d1e3bfb0852230a0316f5efed66dff48b252', '0.0.0.0')]

    locktime = 0

    print (make_transaction(privkeys, inputs, outputs, locktime).hex())


if __name__ == "__main__":
    main()