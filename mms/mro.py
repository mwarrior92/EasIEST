# Measurement Result Object (MRO)
from ..helpers import Extendable
import dns.message
import base64

class PingResult(Extendable):
    def __init__(self, **kwargs):
        self.label = None
        self.af = None # int
        self.dst_addr = None # str
        self.dst_name = None # str
        self.local_addr = None # str
        self.src_addr = None # str
        self.src_name = None # str
        self.rtt_list = list() # list(float)
        self.num_sent = None # int
        self.num_returned = None # int
        self.label = None # str
        self.size = None # int
        self.ttl = None # int
        self.timestamp = None # float
        self.platform = None # str
        for k in kwargs:
            self.set(k, kwargs[k])

    def __repr__(self):
        return "<PingResult: "+str(self.label)+">"

    def __str__(self):
        outstr = str(self.label)+"\n"
        members = [v for v in vars(self) if not callable(v) and not v.startswith("_") and v != "label"]
        for ind, m in enumerate(members):
            if ind % 2 == 0:
                line = "\t" + m + ": " + str(getattr(self, m)) + ",\t\t"
                while len(line) < 30:
                    line += " "
                outstr += line
            else:
                outstr += m + ": " + str(getattr(self, m)) + ",\n"
        return outstr


class PingSetResults(Extendable):
    def __init__(self, **kwargs):
        self.ping_results = list()
        self.raw_file_path = None
        self.file_path = None
        self.label = None
        self.platform = None
        self.meas_type = 'ping'
        for k in kwargs:
            self.set(k, kwargs[k])

    def __repr__(self):
        return "<PingSetResults: "+str(self.label)+", '"+str(self.file_path)+"'>"

    def __str__(self):
        outstr = str(self.label)+"\n"
        outstr += "\tfile_path" + self.file_path + "\n"
        outstr += str(len(self.ping_results)) + " ping results"
        return outstr

    def append(self, result):
        self.ping_results.append(result)


rr_types = {1: 'A', 2: 'NS', 5: 'CNAME', 15: 'MX', 28: 'AAAA'}


class DNSResult(Extendable):
    def __init__(self, **kwargs):
        self.label = None
        self.platform = None
        self.meas_type = 'dns'
        self.query_domain = None
        self.query_type = None
        self.protocol = None
        self.local_resolver = None
        self.target_resolver = None
        self.answers = dict()
        self.raw_response = None
        self.timestamp = None
        self.src_name = None
        self.src_addr = None

        for k in kwargs:
            self.set(k, kwargs[k])

    def extract_answers(self):
        msg = dns.message.from_wire(base64.b64decode(self.raw_response))
        if hasattr(msg, 'answer'):
            self.answers = dict()
            for ans in msg.answer:
                rr_type = rr_types[ans.rdtype]
                self.answers[rr_type] = list()
                for item in ans.items:
                    self.answers[rr_type].append(item.to_text())


class ResultSet(Extendable):
    def __init__(self, **kwargs):
        self.results = list()
        self.raw_file_path = None
        self.file_path = None
        self.label = None
        self.platform = None
        self.meas_type = None
        for k in kwargs:
            self.set(k, kwargs[k])

    def append(self, result):
        self.results.append(result)

