import cryptography as cr

__version__ = '1'


def make_transaction(privkey, pubkey, inputs, outputs, lock_time):
    version = int(__version__) # 4 bytes

    input_count = len(inputs)   # 1+ bytes
    ''' For Each Input '''
    # previous hash 32 bytes
    # index 4 bytes
    # 6a? ??OP_RETURN??
    # len_signature + signature
    # ? hashtype -> SIGHASH_ALL, SIGHASH_NONE, SIGHASH_SINGLE 1 byte
    # len_pubkey + pubkey
    # sequence 4 bytes (0xffffffff)

    output_count = len(outputs) # +1 bytes
    ''' For Each Output '''
    # value satoshis 8 bytes
    # len_script + script (basic len = 19)

    locktime = 0
    return True


def main():
    # TESTS
    privkey = ['2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c',
               '1cb99b78710454890b32a6207e72b335d55e8222e8ec6af5c416f5daf601bc44',
               '84cd947d91cf4b13b573988f829b2573ff4a15eebb1a39c4288ec45ef7dc0b10']
    
    inputs = [('3110b2c2810b6d3a2c558ba62cc305a4b75ddbda6b0204f44d5cb80564c63852', '0'),
              ('d1bd200ecf87320b3f5bb465c7ade141067bc9f1e0623726e1f9a282bb3f3b91', '3'),
              ('3b04a3c1a4155f757374b29786f3f7c43273f7638f5d94b8c38fbd3e4888fbb7', '1')]


if __name__ == "__main__":
    main()