import pytricia
import pickle
from leveldb import LevelDB


class Patricia_state():

    def __init__(self):
        self.patricia = pytricia.PyTricia()
        self.db = LevelDB("./patricia", create_if_missing=True)

    def set_value(self, key, value):
        self.patricia[key] = value

    def get_value(self, key):
        return self.patricia[key]

    def to_db(self):
        obj = pickle.dumps(self.patricia)
        self.db.Put("patricia", obj)

    def from_db(self):
        self.patricia = pickle.loads(self.db.Get("patricia"))
