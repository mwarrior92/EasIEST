import mdo
from ..helpers import Extendable


def build_measurement(**kwargs):
    try:
        mtype = kwargs['measurement_type']
    except KeyError:
        raise ValueError("measurement_type must be defined ('ping', 'dns', etc.)")

    if mtype == 'ping':
        mclass = mdo.ping.Ping
    else:
        raise ValueError("measurement_type must be one of ['ping', 'dns', ...]")

    required_members = mclass.list_required_members()
    missing_members = list()
    for k in required_members:
        if k not in kwargs:
            missing_members.append(k)
    if len(missing_members) > 0:
        raise Exception("the following keyword arguments are required: " +
                        str(missing_members))
    return mclass(**kwargs)


class MDOSequence(Extendable):
    def __init__(self, label, mdo_list, primer_list, callback_list, **kwargs):
        """
        container for a set of MDOs to be performed sequentially, back to back, by a single client
        :param label: (str) brief name describing the MDO sequence
        :param mdo_list: (list(mdo)) list of MDOs to be performed in the order provided
        :param primer_list: (list(func)) list of functions to call on the MDO (using the MDOSequence
        and index as input) before executing the measurement, allowing for dynamically prepared MDOs;
        for example, a ping whose target depends on the outcome of an earlier measurement
        :param callback_list: (list(func)) list of functions to be called after a measurement, (using
        the MDOSequence, the index, and the return var from the function that executed the MDO)
        :param kwargs:

        NOTE: primers MUST take EXACTLY the following parameters:
                    the source MDOSequence, the index
              Additional inputs should be stored inside the MDOSequence in advance as attributes
        NOTE: callbacks MUST take EXACTLY the following parameters:
                    the source MDOSequence, the index, the return from the function that executed the MDO
              Additional inputs should be stored inside the MDOSequence in advance as attributes

        """
        if len(mdo_list) != len(callback_list) or len(mdo_list) != len(primer_list):
            raise ValueError("mdo, prelude, and callback lists must be of the same size")
        for p in primer_list:
            if len(p.__code__.co_varnames) != 2:
                raise ValueError("primers MUST take EXACTLY the following 2 parameters:"
                                 "\t\tthe source MDOSequence, the index\n"
                                 "Additional inputs should be stored inside the MDOSequence in "
                                 "advance as attributes")
        for c in callback_list:
            if len(c.__code__.co_varnames) != 3:
                raise ValueError("callbacks MUST take EXACTLY the following 3 parameters:"
                                 "\t\tthe source MDOSequence, the index, the return from the "
                                 "function that executed the MDO\n"
                                 "Additional inputs should be stored inside the MDOSequence in "
                                 "advance as attributes")
        self.set('label', str(label))
        self.set('mdo_list', mdo_list)
        self.set('index', 0)
        self.set('primer_list', primer_list)
        self.set('callback_list', callback_list)
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __repr__(self):
        return "MDOSequence(" + self.get("label") + ")"

    def __str__(self):
        outstr = "*****************************\n" + "LABEL: " + self.get('label') + "\n"
        outstr += "-----------------------------\n"
        outstr += "MDOs:\n"
        for i, mdoi in enumerate(self.get('mdo_list')):
            outstr += "\tPRELUDE: " + self.get('primer_list')[i].func_name
            outstr += "(" + ", ".join(self.get('primer_list')[i].__code__.co_varnames) + ")" + "\n"
            outstr += "\n".join(["|\t\t"+z for z in str(mdoi).split("\n")]) + "\n"
            outstr += "\tCALLBACK: " + self.get('callback_list')[i].func_name
            outstr += "(" + ", ".join(self.get('callback_list')[i].__code__.co_varnames) + ")" + "\n"
        other_members = [z for z in vars(self) if z not in
                         {["label", "index", "mdo_list", "primer_list", "callback+list"]}]
        if len(other_members) > 0:
            outstr += "-----------------------------\nADDITIONAL INFORMATION:\n"
            for member in other_members:
                outstr += "\t" + member.upper() + ": " + str(self.get(member)) + "\n"
        return outstr+"\n"

    def __iter__(self):
        return self

    def next(self):
        if self.get('index') < len(self.get('mdo_list')):
            mdoi = self.get('mdo_list')[self.get('index')]
            preludei = self.get('primer_list')[self.get('index')]
            callbacki = self.get('callback_list')[self.get('index')]
            index = self.get('index')
            self.set('index', index + 1)
            return {"mdo": mdoi, "prelude": preludei, "callback": callbacki, "index": index}
        else:
            raise StopIteration

    def get_current_mdo(self):
        if self.get('index') < len(self.get('mdo_list')):
            return self.get('mdo_list')[self.get('index')].get_label()
