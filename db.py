import utils
import leveldb
from rlp.utils import str_to_bytes

compress = decompress = lambda x: x
databases = {}


class BaseDB(object):
    pass


class _EphemDB(BaseDB):

    def __init__(self):
        self.db = {}
        self.kv = self.db

    def get(self, key):
        return self.db[key]

    def put(self, key, value):
        self.db[key] = value

    def delete(self, key):
        del self.db[key]

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
            self.kv[key] = self.parent.get(key)
        return self.parent.get(key)

    def put(self, key, value):
        self.parent.put(key, value)

    def commit(self):
        pass

    def delete(self, key):
        self.parent.delete(key)

    def _has_key(self, key):
        return self.parent._has_key(key)

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



def add1(b):
    v = utils.big_endian_to_int(b)
    return utils.zpad(utils.encode_int(v + 1), 4)



def sub1(b):
    v = utils.big_endian_to_int(b)
    return utils.zpad(utils.encode_int(v - 1), 4)


class RefcountDB(BaseDB):

    def __init__(self, db):
        self.db = db
        self.kv = None

    def get(self, key):
        return self.db.get(key)[4:]

    def get_refcount(self, key):
        try:
            return utils.big_endian_to_int(self.db.get(key)[:4])
        except KeyError:
            return 0

    def put(self, key, value):
        try:
            existing = self.db.get(key)
            assert existing[4:] == value
            self.db.put(key, add1(existing[:4]) + value)
            # print('putin', key, utils.big_endian_to_int(existing[:4]) + 1)
        except KeyError:
            self.db.put(key, b'\x00\x00\x00\x01' + value)

    def delete(self, key):
        existing = self.db.get(key)
        if existing[:4] == b'\x00\x00\x00\x01':
            # print('deletung')
            self.db.delete(key)
        else:
            # print(repr(existing[:4]))
            self.db.put(key, sub1(existing[:4]) + existing[4:])

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

class LevelDB(BaseDB):
    """
    filename                                    the database directory
    block_cache_size  (default: 8 * (2 << 20))  maximum allowed size for the block cache in bytes
    write_buffer_size (default  2 * (2 << 20))
    block_size        (default: 4096)           unit of transfer for the block cache in bytes
    max_open_files:   (default: 1000)
    create_if_missing (default: True)           if True, creates a new database if none exists
    error_if_exists   (default: False)          if True, raises and error if the database exists
    paranoid_checks   (default: False)          if True, raises an error as soon as an internal
                                                corruption is detected
    """

    max_open_files = 32000
    block_cache_size = 8 * 1024**2
    write_buffer_size = 4 * 1024**2

    def __init__(self, dbfile):
        self.uncommitted = dict()
        self.dbfile = dbfile
        self.db = leveldb.LevelDB(dbfile, max_open_files=self.max_open_files)
        self.commit_counter = 0

    def reopen(self):
        del self.db
        self.db = leveldb.LevelDB(self.dbfile)

    def get(self, key):
        if key in self.uncommitted:
            if self.uncommitted[key] is None:
                raise KeyError("key not in db")
            return self.uncommitted[key]
        o = decompress(self.db.Get(key))
        self.uncommitted[key] = o
        return o

    def put(self, key, value):
        self.uncommitted[key] = value

    def commit(self):
        batch = leveldb.WriteBatch()
        for k, v in self.uncommitted.items():
            if v is None:
                batch.Delete(k)
            else:
                batch.Put(k, compress(v))
        self.db.Write(batch, sync=False)
        self.uncommitted.clear()
        # self.commit_counter += 1
        # if self.commit_counter % 100 == 0:
        #     self.reopen()

    def delete(self, key):
        self.uncommitted[key] = None

    def _has_key(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __repr__(self):
        return '<DB at %d uncommitted=%d>' % (id(self.db), len(self.uncommitted))

    def inc_refcount(self, key, value):
        self.put(key, value)

    def dec_refcount(self, key):
        pass

    def revert_refcount_changes(self, epoch):
        pass

    def commit_refcount_changes(self, epoch):
        pass

    def cleanup(self, epoch):
        pass

    def put_temporarily(self, key, value):
        self.inc_refcount(key, value)
        self.dec_refcount(key)