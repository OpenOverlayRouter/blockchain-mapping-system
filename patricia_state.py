import pytricia
import pickle
import os


class PatriciaState():

    def __init__(self):
        self.patricia = pytricia.PyTricia()
        self.dic = {}

    def set_value(self, key, value):
        self.patricia[key] = value

    def get_value(self, key):
        return self.patricia[key]

    def to_db(self):
        for key in self.patricia:
            self.dic[key] = self.patricia[key]
        if not os.path.exists((os.path.dirname("./Patricia/patricia.p"))):
            os.makedirs(os.path.dirname("./Patricia/patricia.p"))
        pickle.dump(self.dic, open("./Patricia/patricia.p", "wb"))

    def from_db(self):
        try:
            self.dic = pickle.load(open("./Patricia/patricia.p", "rb"))
        except:
            pass
        for key in self.dic:
            self.patricia[key] = self.dic[key]
