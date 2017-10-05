import json
import os
from random import SystemRandom
import shutil
from uuid import UUID
import keys
from utils import privtopub, sha3, is_string, decode_hex, remove_0x_head

random = SystemRandom()


def mk_privkey(seed):
    return sha3(seed)


def mk_random_privkey():
    k = hex(random.getrandbits(256))[2:-1].zfill(64)
    assert len(k) == 64
    return k.decode('hex')


class Keystore(object):

    def __init__(self, keystore, password=None, path=None):
        self.keystore = keystore
        try:
            self._address = self.keystore['address'].decode('hex')
        except KeyError:
            self._address = None
        self.locked = True
        if password is not None:
            self.unlock(password)
        if path is not None:
            self.path = os.path.abspath(path)
        else:
            self.path = None

    @classmethod
    def new(self, password, key=None, uuid=None, path=None):
        """Create a new account.
        Note that this creates the account in memory and does not store it on disk.
        :param password: the password used to encrypt the private key
        :param key: the private key, or `None` to generate a random one
        :param uuid: an optional id
        """
        if key is None:
            key = mk_random_privkey()
        keystore = keys.make_keystore_json(key, password)
        keystore['id'] = uuid
        return Keystore(keystore, password, path)

    @classmethod
    def load(cls, path, password=None):
        """Load an account from a keystore file.
        :param path: full path to the keyfile
        :param password: the password to decrypt the key file or `None` to leave it encrypted
        """
        with open(path) as f:
            keystore = json.load(f)
        if not keys.check_keystore_json(keystore):
            raise ValueError('Invalid keystore file')
        return Keystore(keystore, password, path=path)

    def dump(self, include_address=True, include_id=True):
        """Dump the keystore for later disk storage.
        The result inherits the entries `'crypto'` and `'version`' from `account.keystore`, and
        adds `'address'` and `'id'` in accordance with the parameters `'include_address'` and
        `'include_id`'.
        If address or id are not known, they are not added, even if requested.
        :param include_address: flag denoting if the address should be included or not
        :param include_id: flag denoting if the id should be included or not
        """
        d = {}
        d['crypto'] = self.keystore['crypto']
        d['version'] = self.keystore['version']
        if include_address and self.address is not None:
            d['address'] = self.address.encode('hex')
        if include_id and self.uuid is not None:
            d['id'] = self.uuid
        return json.dumps(d)

    def unlock(self, password):
        """Unlock the account with a password.
        If the account is already unlocked, nothing happens, even if the password is wrong.
        :raises: :exc:`ValueError` (originating in ethereum.keys) if the password is wrong (and the
                 account is locked)
        """
        if self.locked:
            self._privkey = keys.decode_keystore_json(self.keystore, password)
            self.locked = False
            self.address  # get address such that it stays accessible after a subsequent lock

    def lock(self):
        """Relock an unlocked account.
        This method sets `account.privkey` to `None` (unlike `account.address` which is preserved).
        After calling this method, both `account.privkey` and `account.pubkey` are `None.
        `account.address` stays unchanged, even if it has been derived from the private key.
        """
        self._privkey = None
        self.locked = True

    @property
    def privkey(self):
        """The account's private key or `None` if the account is locked"""
        if not self.locked:
            return self._privkey
        else:
            return None

    @property
    def pubkey(self):
        """The account's public key or `None` if the account is locked"""
        if not self.locked:
            return privtopub(self.privkey)
        else:
            return None

    @property
    def address(self):
        """The account's address or `None` if the address is not stored in the key file and cannot
        be reconstructed (because the account is locked)
        """
        if self._address:
            pass
        elif 'address' in self.keystore:
            self._address = self.keystore['address'].decode('hex')
        elif not self.locked:
            self._address = keys.privtoaddr(self.privkey)
        else:
            return None
        return self._address

    @property
    def uuid(self):
        """An optional unique identifier, formatted according to UUID version 4, or `None` if the
        account does not have an id
        """
        try:
            return self.keystore['id']
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        """Set the UUID. Set it to `None` in order to remove it."""
        if value is not None:
            self.keystore['id'] = value
        elif 'id' in self.keystore:
            self.keystore.pop('id')

    def save(self, store=True, include_address=True, include_id=True):
        if store:
            if self.path is None:
                self.path =  os.path.abspath("./keystore/"+self.address.encode("HEX"))
            assert os.path.isabs(self.path), self.path
            if os.path.exists(self.path):
                raise IOError('File does already exist')
            try:
                directory = os.path.dirname(self.path)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(self.path, 'w') as f:
                    f.write(self.dump(include_address, include_id))
            except IOError as e:
                raise