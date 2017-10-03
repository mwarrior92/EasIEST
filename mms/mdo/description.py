class MeasurementDescription:
    """base container class for measurement descriptions"""
    def __init__(self, **kwargs):
        """
        :param label: (str) a brief label to describe what this particular measurement is at a glance
        """
        self.measurement_type = None
        self.duration = None
        self.repetitions = None
        self.repetition_gap = None
        self.label = kwargs.pop('label')

        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __repr__(self):
        if len(self.label.split()) > 1:
            # force label into camelcase for concise printing (if there are spaces)
            return "mdo(" + "".join(self.label.title().split()) + ")"
        else:
            return "mdo("+self.label+")"

    def __str__(self):
        # we want to print the label first
        outstr = "*****************************\n"+"LABEL: " + self.label + "\n"
        outstr += "-----------------------------\n"
        keys = sorted([z for z in vars(self).keys() if z != 'label'])
        for k in keys:
            outstr += k.upper() + ": " + vars(self)[k] + "\n"
        return outstr

    def get_label(self):
        return self.label

    @staticmethod
    def list_init_members():
        return ["measurement_type", "duration", "repetitions", "repetition_gap", "label"]

    @staticmethod
    def list_required_members():
        return ["label"]

    def get(self, member):
        """
        :param member: (str) name of member whose value should be returned
        :return:
        """
        if hasattr(self, "get_"+member):
            return getattr(self, "get_"+member)()
        else:
            return vars(self)[member]
