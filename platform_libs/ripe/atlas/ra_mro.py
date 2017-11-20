from ....mms import mro

class PingResult(mro.PingResult):
    def set_from(self, addr):
        self.local_addr = addr

    def set_results(self, results):
        self.rtt_list = list()
        for res in results:
            self.rtt_list.append(res['rtt'])

    def set_sent(self, count):
        self.num_sent = count

    def set_rcvd(self, count):
        self.num_returned = count
