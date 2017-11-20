from ....helpers import mydir, logger, format_dirpath
from ....helpers import top_dir
from ....helpers import datestr, timestr
import json
import ripe.atlas.cousteau as rac
from ....cdo import Client, ClientGroup, Location
from ....mms import collector
import datetime
from ra_mro import PingResult

with open(top_dir+'config.json', 'r+') as f:
    config_data = json.load(f)


##############################################################################
# MEASUREMENT CREATION
##############################################################################


def make_ping_test(destinations, af=4, description="ping measurement", **kwargs):
    """

    :param destinations: (list) list of IP (or FQDN) destinations for some measurement set of probes to ping
    :param kwargs: can use ping measurement definitions, as defined in the v2 api reference
    :return: (list) list of ping measurement objects

    NOTE: details for acceptable keyword args can be found at:
            https://atlas.ripe.net/docs/api/v2/reference/#!/measurements/
        in the POST->definitions section of the corresponding measurement type
    """

    pinglist = list()

    for dst in destinations:
        pinglist.append(
            rac.Ping(
                af=af,
                target=dst,
                description=description,
                **kwargs
            )
        )
    return pinglist


def make_traceroute_test(destinations, af=4, protocol="UDP", description="traceroute measurement", **kwargs):
    """
    :param destinations: (list) list of IP (or FQDN) destinations for some measurement set of probes to traceroute
    :param kwargs: can use ping measurement definitions, as defined in the v2 api reference
    :return: (list) list of ping measurement objects

    NOTE: details for acceptable keyword args can be found at:
            https://atlas.ripe.net/docs/api/v2/reference/#!/measurements/
        in the POST->definitions section of the corresponding measurement type
    """

    trlist = list()

    for dst in destinations:
        trlist.append(
            rac.Traceroute(
                af=af,
                target=dst,
                protocol=protocol,
                description=description,
                **kwargs
            )
        )
    return trlist


##############################################################################
# PROBE SELECTION
##############################################################################

def get_probes(**kwargs):
    return rac.ProbeRequest(**kwargs)


def get_usable_probes(**kwargs):
    kwargs['status_name'] = 'Connected'
    kwargs['is_public'] = True
    return get_probes(**kwargs)


def get_TargetLocation_probes(tl):
    kwargs = dict()
    if hasattr(tl, 'coordinate_circle'):
        cc = tl.get_coordinate_circle()
        kwargs['radius'] = cc['radius']
        kwargs['latitude'] = cc['coordinates'][0]
        kwargs['longitude'] = cc['coordinates'][1]
    if hasattr(tl, 'countries'):
        c = tl.get_countries()
        kwargs['country_code__in'] = c
    if hasattr(tl, 'ipv4_subnet'):
        v4s = str(tl.get_ipv4_subnet())
        kwargs['prefix_v4'] = v4s
    if hasattr(tl, 'ipv6_subnet'):
        v6s = str(tl.get_ipv6_subnet())
        kwargs['prefix_v6'] = v6s
    if hasattr(tl, 'v4_asns'):
        v4a = tl.get_v4_asns()
        kwargs['v4_asn__in'] = v4a
    if hasattr(tl, 'v6_asns'):
        v6a = tl.get_v6_asns()
        kwargs['v6_asn__in'] = v6a

    return get_usable_probes(**kwargs)


def probes_to_clients(probes):
    """
    converts list of probes into ClientGroup
    :param probes: (iter) list of probes
    :return: (ClientGroup) group of clients constructed from provided list of probes
    """
    clients = ClientGroup()
    for probe in probes:
        if 'address_v4' in probe:
            probe['ipv4'] = probe['address_v4']
        if 'address_v6' in probe:
            probe['ipv6'] = probe['address_v6']
        if 'id' in probe:
            probe['probe_id'] = probe['id']
        clients.add_client(
            Client(
                platform='ripeatlas',
                location=Location(**probe)
            )
        )
    return clients


def get_TargetLocation_clients(tl):
    probes = get_TargetLocation_probes(tl)
    return probes_to_clients(probes)


def probes_to_ids(probes):
    return [p['id'] for p in probes]


def clients_to_probe_ids(clients):
    return [c.get_probe_id() for c in clients]


##############################################################################
# MEASUREMENT MANAGEMENT
##############################################################################


def make_source(probe_ids):
    str_ids = ""
    for probe_id in probe_ids:
        str_ids += str(probe_id) + ","
    return rac.AtlasSource(
        type="probes",
        value=str_ids[:-1],
        requested=len(probe_ids)
    )


def make_request(measurement, source, **kwargs):
    if 'start_time' not in kwargs:
        kwargs['start_time'] = datetime.datetime.utcnow()+datetime.timedelta(seconds=15)
    if 'key' not in kwargs:
        kwargs['key'] = config_data['ripeatlas_schedule_meas_key']
    if 'tags' not in kwargs:
        kwargs['tags'] = {"include": ["system-ipv4-works"]}

    return rac.AtlasCreateRequest(
        measurements=measurement,
        sources=[source],
        **kwargs
    )


def send_request(probe_ids, measurement, **kwargs):
    source = make_source(probe_ids)
    request = make_request(measurement, source, **kwargs)
    return request.create()


def launch_measurement(probe_ids, measurement, **kwargs):
    is_success, response = send_request(probe_ids, measurement, **kwargs)
    if is_success:
        logger.debug("deployed meas: "+str(response['measurements'][0]))
        return is_success, response
    else:
        logger.warning("failed to deploy: "+str(measurement)+"; "+str(response))
        return False, {}


def raw_ping_retrieval_func(label, msm_id, probe_ids):
    today = datestr(datetime.datetime.utcnow())
    raw_ping_dir = format_dirpath(
            config_data['data_path']+"/raw_data/ripeatlas/"+today+"/")
    fname = raw_ping_dir + label + ".json"
    kwargs = {
        'msm_id': msm_id,
        'probe_ids': probe_ids
    }
    is_success, results = rac.AtlasResultsRequest(**kwargs).create()
    meas = rac.Measurement(id=msm_id)
    print results, msm_id
    if meas.status_id in range(5,8):
        return True, {}, results, fname
    elif len(results) == len(probe_ids):
        with open(fname, "w+") as f:
            json.dump(results, f)
        return True, results, None, fname
    else:
        with open(fname, "w+") as f:
            json.dump(results, f)
        return False, {}, results, fname


def format_ping_results(raw_ping_data, label):
    ret = list()
    for p in raw_ping_data:
        ret.append(PingResult(p))
    return ret

