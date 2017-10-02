import mdo


def build_measurement(**kwargs):
    try:
        mtype = kwargs['measurement_type']
    except KeyError:
        raise Exception("measurement_type must be defined ('ping', 'dns', etc.)")

    if mtype == 'ping':
        mclass = mdo.ping.Ping

    required_members = mclass.list_required_members()
    missing_members = list()
    for k in required_members:
        if k not in kwargs:
            missing_members.append(k)
    if len(missing_members) > 0:
        raise Exception("the following keyword arguments are required: " +
                        str(missing_members))
    return mclass(**kwargs)
