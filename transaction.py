import cryptography as cr

__version__ = '1'   # Must have integer representation


def make_transaction(privkey, pubkey, inputs, outputs, lock_time):
    tx = b''
    tx += int(__version__).to_bytes(length=4, byteorder='little')   # 4 bytes

    input_count = len(inputs)   # 1+ bytes
    if input_count < 253:
        tx += input_count.to_bytes(length=1, byteorder='little')
    elif input_count <= 0xFFFF:
        tx += bytes.fromhex('fd') + input_count.to_bytes(length=2, byteorder='little')
    elif input_count <= 0xFFFFFFFF:
        tx += bytes.fromhex('fe') + input_count.to_bytes(length=4, byteorder='little')
    else:
        tx += bytes.fromhex('ff') + input_count.to_bytes(length=8, byteorder='little')

    tx_out = b''
    output_count = len(outputs) # +1 bytes
    if output_count < 253:
        tx_out += output_count.to_bytes(length=1, byteorder='little')
    elif output_count <= 0xFFFF:
        tx_out += bytes.fromhex('fd') + output_count.to_bytes(length=2, byteorder='little')
    elif output_count <= 0xFFFFFFFF:
        tx_out += bytes.fromhex('fe') + output_count.to_bytes(length=4, byteorder='little')
    else:
        tx_out += bytes.fromhex('ff') + output_count.to_bytes(length=8, byteorder='little')
    ''' For Each Output '''
    # value satoshis 8 bytes
    # len_script + script (basic len = 19)
    

    ''' For Each Input '''
    for i, input in enumerate(inputs):
        # previous hash, 32 bytes
        tx_in = bytes.fromhex(input[0])
        # index, 4 bytes
        tx_in += int(input[1]).to_bytes(length=4, byteorder='little')

        prev_script = '0000000000000000'

        pubkey = cr.privkey_to_pubkey(privkey[i])
        pubkey = cr.compress_pubkey(pubkey)
    
    # len ScriptSign
    # len_signature + signature
    # ? hashtype -> SIGHASH_ALL, SIGHASH_NONE, SIGHASH_SINGLE 1 byte
    # len_pubkey + pubkey
    # sequence 4 bytes (0xffffffff)

    locktime = 0
    return tx


def main():
    # TESTS
    privkey = ['2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c',
               '1cb99b78710454890b32a6207e72b335d55e8222e8ec6af5c416f5daf601bc44',
               '84cd947d91cf4b13b573988f829b2573ff4a15eebb1a39c4288ec45ef7dc0b10']
    
    inputs = [('3110b2c2810b6d3a2c558ba62cc305a4b75ddbda6b0204f44d5cb80564c63852', '0'),
              ('d1bd200ecf87320b3f5bb465c7ade141067bc9f1e0623726e1f9a282bb3f3b91', '3'),
              ('3b04a3c1a4155f757374b29786f3f7c43273f7638f5d94b8c38fbd3e4888fbb7', '1')]

    print (make_transaction(privkey, [], inputs, [], 0).hex())


if __name__ == "__main__":
    main()