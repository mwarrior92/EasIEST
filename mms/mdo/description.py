class MeasurementDescription:
    """base container class for measurement descriptions"""
    def __init__(self):
        self.measurement_type = None
        self.duration = None
        self.repetitions = None
        self.repetition_gap = None

    def set_type(self, mtype):
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