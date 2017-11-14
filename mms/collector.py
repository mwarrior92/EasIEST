import threading
from time import sleep


class SpinningCollector:
    def __init__(self, meas_label, retrieval_func, callback, spin_time=30):
        self.label = meas_label
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
            self.result_obtained, self.result, self.err = self.retrieval_func()
            if self.result_obtained:
                self.callback(self)
                return
            else:
                sleep(self.spin_time)


class TriggeredCollector:
    def __init__(self, meas_label, retrieval_func, trigger_event, callback, timeout=None):
        self.label = meas_label
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
        self.result_obtained, self.result, self.err = self.retrieval_func()
        self.callback(self)


def wait_on_collectors(collectors, max_remaining_threads=0, timeout=300):
    if threading.activeCount() > max_remaining_threads:
        for collector in collectors:
            collector.grabber_thread.join()

