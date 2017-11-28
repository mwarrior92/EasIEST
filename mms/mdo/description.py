from ...helpers import Extendable
from ... import platform_libs


class MeasurementDescription(Extendable):
    """base container class for measurement descriptions"""
    def __init__(self, label, **kwargs):
        """
        :param label: (str) a brief label to describe what this particular measurement is at a glance
        """
        self.label = label
        for k in kwargs:
            self.set(k, kwargs[k])

    def __repr__(self):
        if len(self.label.split()) > 1:
            # force label into camelcase for concise printing (if there are spaces)
            return "mdo(" + "".join(self.label.title().split()) + ")"
        else:
            return "mdo("+self.label+")"

    def __str__(self):
        # we want to print the label first
        outstr = "*****************************\n"+"LABEL: " + self.get_label() + "\n"
        outstr += "-----------------------------\n"
        keys = sorted([z for z in vars(self).keys() if z != 'label'])
        for k in keys:
            outstr += k.upper() + ": " + vars(self)[k] + "\n"
        return outstr

    def get_label(self):
        return self.label

    def format_to_platform(self, platform):
        pl = getattr(platform_libs, platform)
        return pl.format_mdo(self)
