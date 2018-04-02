from ...helpers import logger, format_dirpath
from ...helpers import top_dir
from ...helpers import nowstr, timestr
import json
import ripe.atlas.cousteau as rac
from ...cdo import Client, ClientGroup, Location
import datetime
from ra_mro import PingResult, DNSResult
from ...mms.mro import PingSetResults, ResultSet
from collections import defaultdict
from copy import deepcopy
from time import sleep

with open(top_dir+'config.json', 'r+') as f:
    config_data = json.load(f)


##############################################################################
# MEASUREMENT CREATION
##############################################################################


def make_ping_struct(destinations, af=4, description="ping measurement", is_oneoff=True, resolve_on_probe=True,
                     is_public=True, **kwargs):
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
                is_oneoff=is_oneoff,
                resolve_on_probe=resolve_on_probe,
                is_public=is_public,
                **kwargs
            )
        )
    return pinglist


def make_dns_struct(query_domains, description="dns measurement", af=4, is_oneoff=True, use_probe_resolver=True,
                    query_type='A', include_qbuf=True, include_abuf=True, set_nsid_bit=True, is_public=True,
                    query_class='IN', **kwargs):
    dnslist = list()
    for dom in query_domains:
        dnslist.append(
            rac.Dns(
                query_argument=dom,
                description=description,
                af=af,
                is_oneoff=is_oneoff,
                use_probe_resolver=use_probe_resolver,
                query_type=query_type,
                include_qbuf=include_qbuf,
                include_abuf=include_abuf,
                set_nsid_bit=set_nsid_bit,
                is_public=is_public,
                query_class=query_class,
                **kwargs
            )
        )
    return dnslist



def make_traceroute_struct(destinations, af=4, protocol="UDP",
                                description="traceroute measurement", **kwargs):
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


def format_mdo(measdo):
    meas_type = measdo.get('meas_type')
    if meas_type == 'ping':
        with open(top_dir+'platform_libs/ripe_atlas/ping_request_schema.json', 'r+') as f:
            schema = json.load(f)
        valid_params = schema.keys()
        kwargs = {
            'destinations': measdo.destinations,
            'packets': measdo.repetitions,
            'description': measdo.label,
        }
        # TODO: add packet_interval to kwargs; if it's too low, most probes can't actually succeed
        for m in [v for v in vars(measdo) if not callable(v) and not v.startswith('_')]:
            if m in valid_params:
                kwargs[m] = getattr(measdo, m)
        return make_ping_struct(**kwargs)
    if meas_type == 'dns':
        with open(top_dir+'platform_libs/ripe_atlas/dns_request_schema.json', 'r+') as f:
            schema = json.load(f)
        valid_params = schema.keys()
        kwargs = {
            'query_domains': measdo.query_domains,
            'description': measdo.label,
        }
        if measdo.get('target_resolver') is not None:
            kwargs['target'] = measdo.get('target_resolver')
            kwargs['use_probe_resolver'] = False

        for m in [v for v in vars(measdo) if not callable(v) and not v.startswith('_')]:
            if m in valid_params:
                kwargs[m] = getattr(measdo, m)
        return make_dns_struct(**kwargs)

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
        cc = tl.get('coordinate_circle')
        kwargs['radius'] = cc['radius']
        kwargs['latitude'] = cc['coordinates'][0]
        kwargs['longitude'] = cc['coordinates'][1]
    if hasattr(tl, 'countries'):
        c = tl.get('countries')
        kwargs['country_code__in'] = c
    if hasattr(tl, 'ipv4_subnet'):
        v4s = str(tl.get('ipv4_subnet'))
        kwargs['prefix_v4'] = v4s
    if hasattr(tl, 'ipv6_subnet'):
        v6s = str(tl.get('ipv6_subnet'))
        kwargs['prefix_v6'] = v6s
    if hasattr(tl, 'v4_asns'):
        v4a = tl.get('v4_asns')
        kwargs['v4_asn__in'] = v4a
    if hasattr(tl, 'v6_asns'):
        v6a = tl.get('v6_asns')
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
        mems = probe.keys()
        for k in mems:
            if probe[k] is None:
                del probe[k]
        clients.add_client(
            Client(
                platform='ripe_atlas',
                location=Location(**probe)
            )
        )
    return clients


def get_TargetLocation_clients(tl):
    probes = get_TargetLocation_probes(tl)
    return probes_to_clients(probes)


def probes_to_ids(probes):
    return [p['id'] for p in probes]


def clients_to_probe_ids(client_group):
    clients = client_group.get('clients')
    return [c.get('location').get('probe_id') for c in clients]


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
        return is_success, False, response
    else:
        logger.warning("failed to deploy: "+str(measurement)+"; "+str(response))
        print str(measurement[0])
        if "more than" in json.dumps(response) or "more than" in \
            str(measurement[0]):
                return False, True, {}

        return False, False, {}


def dispatch_measurement(clients, measdo, **kwargs):
    measurement = format_mdo(measdo)
    if measdo.get('meas_type') == 'ping':
        rfp = format_dirpath(config_data['data_path']+"/raw_data/ripe_atlas/"+nowstr()+"/ping")
        rfp += measdo.get('label') + timestr(datetime.datetime.utcnow()) + ".json"
        res = ResultSet(platform='ripe_atlas', raw_file_path=rfp, label=measdo.get('label'), meas_type='ping', **kwargs)
    elif measdo.get('meas_type') == 'dns':
        rfp = format_dirpath(config_data['data_path']+"/raw_data/ripe_atlas/"+nowstr()+"/dns")
        rfp += measdo.get('label') + timestr(datetime.datetime.utcnow()) + ".json"
        res = ResultSet(platform='ripe_atlas', raw_file_path=rfp, label=measdo.get('label'), meas_type='dns',
                        target_resolver=measdo.get('target_resolver'), **kwargs)

    probe_ids = clients_to_probe_ids(clients)
    # print probe_ids
    is_success, slowdown, response = launch_measurement(probe_ids, measurement)
    res.set('slow_down', slowdown)
    res.set('is_success', is_success)
    if is_success:
        res.set('msm_ids', response['measurements'])
        res.set('running_msm_ids', response['measurements'])
        res.set('probe_ids', probe_ids)
    print response
    return res


##############################################################################
# COLLECTOR FUNCTIONS
##############################################################################


def ping_retrieval_func(collector):
    allresults = dict()
    probe_ids = collector.measro.get('probe_ids')
    raw_file_path = collector.measro.get('raw_file_path')
    all_ids = collector.measro.get('running_msm_ids')
    running_msm_ids = set(deepcopy(all_ids))
    attempts = defaultdict(int)
    max_attempts = max([1, (collector.timeout / collector.spin_time)])
    things_left = len(running_msm_ids)
    while things_left > 0:
        for msm_id in all_ids:
            if msm_id in running_msm_ids:
                attempts[msm_id] += 1
                kwargs = {
                    'msm_id': msm_id,
                    'probe_ids': probe_ids
                }
                is_success, results = rac.AtlasResultsRequest(**kwargs).create()
                if attempts[msm_id] < max_attempts:
                    meas = rac.Measurement(id=msm_id)
                    if meas.status_id in range(5, 8):  # give up if there was an error
                        running_msm_ids.remove(msm_id)  # we don't need to check it again if it's err'd
                        allresults[msm_id] = {
                            'result':None,
                            'err': results
                        }
                    elif len(results) == len(probe_ids):  # finish if all results have been obtained
                        running_msm_ids.remove(msm_id)  # we don't need to check it again if it's done
                        allresults[msm_id] = {
                            'result': results,
                            'err': None
                        }
                    else:
                        allresults[msm_id] = {
                            'result': results,
                            'err': None
                        }
                else:
                    running_msm_ids.remove(msm_id)  # if we've made the max attempts, give up
                    allresults[msm_id] = {
                        'result': results,
                        'err': None
                    }
        things_left = len(running_msm_ids)
        if things_left > 0:
            collector.time_elapsed += collector.spin_time
            sleep(collector.spin_time)

    # format for output to collector
    res = list()
    errs = list()
    for msm_id in all_ids:
        if msm_id in allresults:
            res.append(allresults[msm_id]['result'])
            errs.append(allresults[msm_id]['err'])
        else:
            res.append(None)
            errs.append({'err': 'no result...'})
    with open(raw_file_path, "w+") as f:
        json.dump(res, f)
    return True, res, errs


def dns_retrieval_func(collector):
    allresults = dict()
    probe_ids = collector.measro.get('probe_ids')
    raw_file_path = collector.measro.get('raw_file_path')
    all_ids = collector.measro.get('running_msm_ids')
    running_msm_ids = set(deepcopy(all_ids))
    attempts = defaultdict(int)
    max_attempts = max([1, (collector.timeout / collector.spin_time)])
    things_left = len(running_msm_ids)
    while things_left > 0:
        for msm_id in all_ids:
            if msm_id in running_msm_ids:
                attempts[msm_id] += 1
                kwargs = {
                    'msm_id': msm_id,
                    'probe_ids': probe_ids
                }
                is_success, results = rac.AtlasResultsRequest(**kwargs).create()
                if attempts[msm_id] < max_attempts:
                    meas = rac.Measurement(id=msm_id)
                    if meas.status_id in range(5, 8):  # give up if there was an error
                        running_msm_ids.remove(msm_id)  # we don't need to check it again if it's err'd
                        allresults[msm_id] = {
                            'result':None,
                            'err': results
                        }
                    elif len(results) == len(probe_ids):  # finish if all results have been obtained
                        running_msm_ids.remove(msm_id)  # we don't need to check it again if it's done
                        allresults[msm_id] = {
                            'result': results,
                            'err': None
                        }
                    else:
                        allresults[msm_id] = {
                            'result': results,
                            'err': None
                        }
                else:
                    running_msm_ids.remove(msm_id)  # if we've made the max attempts, give up
                    allresults[msm_id] = {
                        'result': results,
                        'err': None
                    }
        things_left = len(running_msm_ids)
        if things_left > 0:
            collector.time_elapsed += collector.spin_time
            sleep(collector.spin_time)

    # format for output to collector
    res = list()
    errs = list()
    for msm_id in all_ids:
        if msm_id in allresults:
            res.append(allresults[msm_id]['result'])
            errs.append(allresults[msm_id]['err'])
        else:
            res.append(None)
            errs.append({'err': 'no result...'})
    with open(raw_file_path, "w+") as f:
        json.dump(res, f)
    return True, res, errs


def ping_callback(collector):
    for results, err in zip(collector.get('result_data'), collector.get('err')):
        if err is None:
            for res in results:
                collector.measro.append(format_ping_result(res))
        else:
            logger.warning(str(err))
    collector.measro.save_json()


def dns_callback(collector):
    for results, err in zip(collector.get('result_data'), collector.get('err')):
        if err is None:
            for res in results:
                collector.measro.append(format_dns_result(res))
        else:
            logger.warning(str(err))
    collector.measro.save_json()


def format_ping_result(raw_ping_data):
    return PingResult(platform='ripe_atlas', **raw_ping_data)


def format_dns_result(rawdat):
    return DNSResult(platform='ripe_atlas', **rawdat)


