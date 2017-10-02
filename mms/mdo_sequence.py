import mdo


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


class MDOSequence:
    def __init__(self, mdo_list, preludes, handlers, **kwargs):
        self.mdo_list = mdo_list
        self.index = 0
        self.return_data = list()
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __iter__(self):
        return self

    def next(self):
        if self.index < len(self.mdo_list):
            self.index += 1
            return self.mdo_list[self.index - 1]
        else:
            raise StopIteration

    def get_current_MDO(self):
        if self.index < len(self.mdo_list):
            return self.mdo_list[self.index].get_label()


class Experiment:
    def __init__(self):
        self.sequences = list()