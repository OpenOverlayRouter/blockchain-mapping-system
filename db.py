from ethereum import utils
from ethereum.slogging import get_logger
from rlp.utils import str_to_bytes
import sys
if sys.version_info.major == 2:
    from repoze.lru import lru_cache
else:
    from functools import lru_cache

log = get_logger('db')


databases = {}


class BaseDB(object):
    pass


class _EphemDB(BaseDB):

    def __init__(self):
        self.db = {}
        self.kv = self.db

    def get(self, key):
        try:
            return self.db.Get(key)
        except KeyError:
            print("leveldb get error")

    def put(self, key, value):
        try:
            return self.db.Put(key, value)
        except KeyError:
            print("leveldb put error")

    def delete(self, key):
        try:
            return self.db.Delete(key)
        except KeyError:
            print("leveldb delete error")

    def commit(self):
        pass

    def _has_key(self, key):
        return key in self.db

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __hash__(self):
        return utils.big_endian_to_int(str_to_bytes(self.__repr__()))


DB = EphemDB = _EphemDB


# Used for SPV proof creation
class ListeningDB(BaseDB):

    def __init__(self, db):
        self.parent = db
        self.kv = {}

    def get(self, key):
        if key not in self.kv:
            try:
                self.kv[key] = self.parent.Get(key)
            except KeyError:
                print("leveldb get error")
        try:
            return self.parent.Get(key)
        except KeyError:
            print("leveldb get error")

    def put(self, key, value):
        try:
            self.parent.Put(key, value)
        except KeyError:
            print("leveldb put error")

    def commit(self):
        pass

    def delete(self, key):
        try:
            self.parent.Delete(key)
        except KeyError:
            print("leveldb delete error")

    def _has_key(self, key):
        try:
            if (self.parent.Get(key) is None):
                return False
            return True
        except KeyError:
            print("leveldb get error")

    def __contains__(self, key):
        return self.parent.__contains__(key)

    def __eq__(self, other):
        return self.parent == other

    def __hash__(self):
        return self.parent.__hash__()


# Used for making temporary objects
class OverlayDB(BaseDB):

    def __init__(self, db):
        self.db = db
        self.kv = None
        self.overlay = {}

    def get(self, key):
        if key in self.overlay:
            if self.overlay[key] is None:
                raise KeyError()
            return self.overlay[key]
        return self.db.get(key)

    def put(self, key, value):
        self.overlay[key] = value

    def delete(self, key):
        self.overlay[key] = None

    def commit(self):
        pass

    def _has_key(self, key):
        if key in self.overlay:
            return self.overlay[key] is not None
        return key in self.db

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __hash__(self):
        return utils.big_endian_to_int(str_to_bytes(self.__repr__()))


@lru_cache(128)
def add1(b):
    v = utils.big_endian_to_int(b)
    return utils.zpad(utils.encode_int(v + 1), 4)


@lru_cache(128)
def sub1(b):
    v = utils.big_endian_to_int(b)
    return utils.zpad(utils.encode_int(v - 1), 4)


class RefcountDB(BaseDB):

    def __init__(self, db):
        self.db = db
        self.kv = None

    def get(self, key):
        return self.db.Get(key)[4:]

    def get_refcount(self, key):
        try:
            return utils.big_endian_to_int(self.db.Get(key)[:4])
        except KeyError:
            return 0

    def put(self, key, value):
        try:
            existing = self.db.Get(key)
            assert existing[4:] == value
            self.db.Put(key, add1(existing[:4]) + value)
            # print('putin', key, utils.big_endian_to_int(existing[:4]) + 1)
        except KeyError:
            self.db.Put(key, b'\x00\x00\x00\x01' + value)
            # print('putin', key, 1)

    def delete(self, key):
        existing = self.db.Get(key)
        if existing[:4] == b'\x00\x00\x00\x01':
            # print('deletung')
            self.db.Delete(key)
        else:
            # print(repr(existing[:4]))
            self.db.Put(key, sub1(existing[:4]) + existing[4:])

    def commit(self):
        pass

    def _has_key(self, key):
        return key in self.db

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __hash__(self):
        return utils.big_endian_to_int(str_to_bytes(self.__repr__()))