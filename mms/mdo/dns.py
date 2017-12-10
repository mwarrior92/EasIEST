import description


class DNS(description.MeasurementDescription):
    """container class for DNS measurment descriptions"""
    def __init__(self, label, query_domains, query_type='A', protocol='UDP', target_resolver=None, meas_type='dns', **kwargs):
        description.MeasurementDescription.__init__(self, label=label, meas_type=meas_type, query_domains=query_domains,
                                                    target_resolver=target_resolver, protocol=protocol,
                                                    query_type=query_type, **kwargs)


