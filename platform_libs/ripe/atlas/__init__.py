import signal
from ....helpers import timeout_handler
from ....helpers import mydir
from ....helpers import logger
import json
import ripe.atlas.cousteau as rac
from ....cdo import Client, ClientGroup, Location

with open(mydir()+'ripeatlas_config.json.json', 'r+') as f:
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
    clients = ClientGroup()
    for probe in probes:
        clients.add_client(
            Client(
                platform='ripe_atlas',
                location=Location(
                    country=probe['country_code'],
                    asn=probe['asn_v4']
                )
            )
        )