import signal
from ....helpers import timeout_handler
from ....helpers import mydir
from ....helpers import logger
from ....helpers import Extendable
import json
import ripe.atlas.cousteau as rac
from ....cdo import Client, ClientGroup, Location
from ....mms import collector
import datetime

with open(mydir()+'ripeatlas_config.json', 'r+') as f:
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

def get_all_probes(**kwargs):
    return rac.ProbeRequest(**kwargs)


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
        clients.add_client(
            Client(
                platform='ripe_atlas',
                location=Location(**probe)
            )
        )
    return clients


def probes_to_ids(probes):
    return [p['id'] for p in probes]


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
        kwargs['key'] = config_data['schedule_meas_key']
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
            logger.debug("deployed meas: "+response['measurements'][0])
            return is_success, response
        else:
            logger.warning("failed to deploy: "+str(measurement)+"; "+str(response))
            return False, {}

