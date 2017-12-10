from ...mms import mro
import dns.message
import base64

class PingResult(mro.PingResult):
    def set_from(self, addr):
        self.src_addr = addr

    def set_src_addr(self, addr):
        self.local_addr = addr

    def set_result(self, results):
        self.rtt_list = list()
        for res in results:
            self.rtt_list.append(res['rtt'])

    def set_sent(self, count):
        self.num_sent = count

    def set_rcvd(self, count):
        self.num_returned = count


class DNSResult(mro.DNSResult):
    def set_from(self, addr):
        self.src_addr = addr

    def set_src_addr(self, addr):
        self.local_addr = addr

    def set_dst_addr(self, addr):
        self.local_resolver = addr

    def set_dst_name(self, name):
        self.local_resolver_name = name

    def set_query_argument(self, val):
        self.query_domain = val

    def set_target(self, val):
        self.resolver = val

    def set_proto(self, proto):
        self.protocol = proto

    def set_result(self, res):
        for k in res:
            self.set(k, res[k])

    def set_resultset(self, res):
        for k in res[0]: # NOTE: I assume these are only oneoff experiments
            self.set(k, res[0][k])

    def set_abuf(self, abuf):
        self.raw_response = abuf
        self.extract_answers()

    def set_qbuf(self, qbuf):
        self.raw_query = qbuf
        d = dns.message.from_wire(base64.b64decode(qbuf))
        if hasattr(d, 'question'):
            self.query_domain = d.question[0].name.to_text()
            self.query_type = mro.rr_types[d.question[0].rdtype]

    def set_rt(self, rt):
        self.response_time = rt