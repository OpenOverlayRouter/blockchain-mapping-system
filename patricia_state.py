import radix
import pickle
import os



class PatriciaState():

    def __init__(self):
        self.patricia = radix.Radix()
        self.dic = {}

    def set_value(self, key, value):
        rnode = self.patricia.add(key)
        rnode.data["address"] = value

    def get_value(self, key):
        rnode = self.patricia.search_best(key)
        return rnode.data["address"]

    def to_db(self):
        for node in self.patricia.nodes():
            self.dic[node.prefix] = self.get_value(node.prefix)
        if not os.path.exists((os.path.dirname("./Patricia/patricia.p"))):
            os.makedirs(os.path.dirname("./Patricia/patricia.p"))
        pickle.dump(self.dic, open("./Patricia/patricia.p", "wb"))

    def from_db(self):
        try:
            self.dic = pickle.load(open("./Patricia/patricia.p", "rb"))
        except:
            pass
        for key in self.dic:
            self.set_value(key,self.dic[key])
