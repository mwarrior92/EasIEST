import threading
from time import sleep
from ..helpers import mydir, format_dirpath, top_dir, Extendable
from .. import platform_libs
import json

with open(top_dir+"config.json", 'r+') as f:
    config_data = json.load(f)

class SpinningCollector(Extendable):
    def __init__(self, measro, retrieval_func=None, callback=None, spin_time=10,
            timeout=90):
        """

        :param meas_kwargs: (dict) will be used as input for retrieval_func
        :param retrieval_func: function to retrieve measurement from file; will use label as parameter input
        :param callback: function to call once measurement has been obtained
        :param spin_time: time to wait between attempts to retrieve measurement results
        """

        self.measro = measro
        self.retrieval_func = retrieval_func
        self.callback = callback

        if self.retrieval_func is None:
            self.set_retrieval_func(self.measro.get('meas_type'))
        if self.callback is None:
            self.set_callback(self.measro.get('meas_type'))

        self.result_obtained = False
        self.spin_time = spin_time
        self.result_data = None
        self.err = None
        self.filename = None
        self.time_elapsed = 0
        self.timeout = timeout

        self.grabber_thread = threading.Thread(target=self.get_result)
        self.grabber_thread.daemon = True
        self.grabber_thread.start()


    def set_retrieval_func(self, meas_type):
        func_name = meas_type+'_retrieval_func'
        pl = getattr(platform_libs, self.measro.get('platform'))
        self.retrieval_func = getattr(pl, func_name)

    def set_callback(self, meas_type):
        func_name = meas_type+'_callback'
        pl = getattr(platform_libs, self.measro.get('platform'))
        self.callback = getattr(pl, func_name)

    def get_result(self):
        print "spinning..."
        while True:
            print "loop..."
            self.result_obtained, self.result_data, self.err = self.retrieval_func(self)
            print "ran func"
            if self.result_obtained:
                print "got res"
                self.callback(self)
                return
            elif self.time_elapsed >= self.timeout:
                print "timed out"
                self.callback(self)
                return
            else:
                print "sleeping..."
                self.time_elapsed += self.spin_time
                sleep(self.spin_time)
            print "idk"


class TriggeredCollector(Extendable):
    def __init__(self, measro, trigger_event, retrieval_func=None,
                 callback=None, timeout=None):
        """

        :param meas_kwargs: (dict) will be used as input for retrieval_func
        :param retrieval_func: function to retrieve measurement from file; will use label as parameter input
        :param trigger_event: the event to listen for; once the event has been observed, call retrieval func
        :param callback: function to call once measurement has been obtained
        :param timeout: time to wait for trigger before giving up
        """
        self.measro = measro
        self.trigger_event = trigger_event
        self.retrieval_func = retrieval_func
        self.callback = callback

        if self.retrieval_func is None:
            self.set_retrieval_func(self.measro.get('meas_type'))
        if self.callback is None:
            self.set_callback(self.measro.get('meas_type'))

        self.result = None
        self.err = None
        self.result_obtained = False
        self.timeout = timeout
        self.filename = None
        self.grabber_thread = threading.Thread(target=self.get_result)
        self.grabber_thread.daemon = True
        self.grabber_thread.start()

    def set_retrieval_func(self, meas_type):
        func_name = meas_type+'_retrieval_func'
        pl = getattr(platform_libs, self.measro.get('platform'))
        self.retrieval_func = getattr(pl, func_name)

    def set_callback(self, meas_type):
        func_name = meas_type+'_callback'
        pl = getattr(platform_libs, self.measro.get('platform'))
        self.callback = getattr(pl, func_name)

    def get_result(self):
        self.trigger_event.wait(self.timeout)
        self.trigger_event.clear()
        self.result_obtained, self.result, self.err = self.retrieval_func(self)
        self.callback(self)


def wait_on_collectors(collectors, timeout=None):
    for collector in collectors:
        if timeout is None:
            collector.grabber_thread.join()
        else:
            collector.grabber_thread.join(timeout)
