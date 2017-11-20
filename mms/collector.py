import threading
from time import sleep
from ..helpers import mydir, format_dirpath
import json

with open(format_dirpath(mydir()+"../config.json"), 'r+') as f:
    config_data = json.load(f)

class SpinningCollector:
    def __init__(self, meas_kwargs, retrieval_func, callback, spin_time=30):
        """

        :param meas_kwargs: (dict) will be used as input for retrieval_func
        :param retrieval_func: function to retrieve measurement from file; will use label as parameter input
        :param callback: function to call once measurement has been obtained
        :param spin_time: time to wait between attempts to retrieve measurement results
        """
        self.meas_kwargs = meas_kwargs
        self.retrieval_func = retrieval_func
        self.result_obtained = False
        self.callback = callback
        self.spin_time = spin_time
        self.result = None
        self.err = None
        self.grabber_thread = threading.Thread(target=self.get_result)
        self.grabber_thread.daemon = True
        self.grabber_thread.start()

    def get_result(self):
        while True:
            self.result_obtained, self.result, self.err = self.retrieval_func(**self.meas_kwargs)
            if self.result_obtained:
                self.callback(self)
                return
            else:
                sleep(self.spin_time)


class TriggeredCollector:
    def __init__(self, meas_kwargs, retrieval_func, trigger_event, callback, timeout=None):
        """

        :param meas_kwargs: (dict) will be used as input for retrieval_func
        :param retrieval_func: function to retrieve measurement from file; will use label as parameter input
        :param trigger_event: the event to listen for; once the event has been observed, call retrieval func
        :param callback: function to call once measurement has been obtained
        :param timeout: time to wait for trigger before giving up
        """
        self.meas_kwargs = meas_kwargs
        self.trigger_event = trigger_event
        self.retrieval_func = retrieval_func
        self.callback = callback
        self.result = None
        self.err = None
        self.result_obtained = False
        self.timeout = timeout
        self.grabber_thread = threading.Thread(target=self.get_result)
        self.grabber_thread.daemon = True
        self.grabber_thread.start()

    def get_result(self):
        self.trigger_event.wait(self.timeout)
        self.trigger_event.clear()
        self.result_obtained, self.result, self.err = self.retrieval_func(self.meas_kwargs)
        self.callback(self)


def wait_on_collectors(collectors, timeout=300):
    for collector in collectors:
        collector.grabber_thread.join(timeout)
