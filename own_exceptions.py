class VerificationFailed(Exception):
    pass


class InvalidTransaction(Exception):
    pass


class UnsignedTransaction(InvalidTransaction):
    pass


class InvalidNonce(InvalidTransaction):
    pass


class InsufficientBalance(InvalidTransaction):
    pass

class UncategorizedTransaction(InvalidTransaction):
    pass

class InvalidCategory(InvalidTransaction):
    pass

class InvalidBlock(Exception):
    pass

class UnsignedBlock(InvalidBlock):
    pass

class InvalidBlockSigner(InvalidBlock):
    pass