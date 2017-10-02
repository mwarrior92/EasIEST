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
        outstr = "*****************************"+"LABEL: " + self.label + "\n"
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

    def set_measurement_type(self, mtype):
        """
        set the measurement type
        :param mtype: (str) ping, download, dns, http, https, etc...
        """
        self.measurement_type = mtype

    def set_duration(self, dur):
        """
        set the duration
        :param dur: (float) the amount of time you want the measurement to last
        """

        self.duration = dur

    def set_repetitions(self, reps):
        """
        set the number of times the measurement will repeat back-to-back
        :param reps: (int) # repetitions
        """

        self.repetitions = reps

    def set_repetition_gap(self, gap):
        """
        set the amount of time (in seconds) between each repetition of the measurement
        :param gap: (float) gap (in seconds) between back-to-back repetitions
        """

        self.repetition_gap = gap
