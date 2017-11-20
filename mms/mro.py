# Measurement Result Object (MRO)
from ..helpers import Extendable
import json

class PingResult(Extendable):
    def __init__(self, **kwargs):
        self.af = None # int
        self.dst_addr = None # str
        self.dst_name = None # str
        self.local_addr = None # str
        self.src_addr = None # str
        self.src_name = None # str
        self.rtt_list = None # list(float)
        self.num_sent = None # int
        self.num_returned = None # int
        self.label = None # str
        self.size = None # int
        self.ttl = None # int
        self.timestamp = None # float
        for k in kwargs:
            self.set(k, kwargs[k])

    def get_json(self):
        ret = dict()
        for k in [z for z in vars(self).keys if not \
                callable(getattr(self,z)) and not z.startswith("__")]:
            ret[k] = self.get(k)
        return ret

    def save_json(self, fpath):
        data = self.get_json()
        with open(fpath, "w+") as f:
            json.dump(data, f)
