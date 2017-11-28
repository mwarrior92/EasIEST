import description


class Ping(description.MeasurementDescription):
    """container class for ping measurement descriptions"""
    def __init__(self, label, measurement_type='ping', duration=9, reptitions=3,
                 repetition_gap=0, destinations=None, af=4, **kwargs):
        kwargs['meas_type'] = measurement_type
        kwargs['destinations'] = destinations
        kwargs['duration'] = duration
        kwargs['repetitions'] = reptitions
        kwargs['repetition_gap'] = repetition_gap
        kwargs['label'] = label
        kwargs['af'] = af
        description.MeasurementDescription.__init__(self, **kwargs)
