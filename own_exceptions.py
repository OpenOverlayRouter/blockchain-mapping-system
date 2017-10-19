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

class InsufficientStartGas(InvalidTransaction):
    pass


class BlockGasLimitReached(InvalidTransaction):
    pass


class GasPriceTooLow(InvalidTransaction):
    pass