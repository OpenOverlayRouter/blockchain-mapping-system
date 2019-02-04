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

class DkgBlockRequiresGroupKey(Exception):
    pass

#For DKG and BLS
#DKG errors
class DkgAddContributionSharesError(Exception):
    pass

class DkgAddVerificationVectorsError(Exception):
    pass

class DkgGenKeysError(Exception):
    pass

class DkgGenerateSecretKeyShareError(Exception):
    pass
#BLS Errors
class BlsInvalidGroupSignature(Exception):
    pass

class BlsSignError(Exception):
    pass

class BlsRecoverError(Exception):
    pass