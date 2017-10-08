import description


class Ping(description.MeasurementDescription):
    """container class for ping measurement descriptions"""
    def __init__(self, label, measurement_type='ping', duration=9, reptitions=3, repetition_gap=0, target=None, **kwargs):
        kwargs['measurement_type'] = measurement_type
        kwargs['target'] = target
        kwargs['duration'] = duration
        kwargs['repetitions'] = reptitions
        kwargs['repetition_gap'] = repetition_gap
        kwargs['label'] = label
        description.MeasurementDescription.__init__(self, **kwargs)
