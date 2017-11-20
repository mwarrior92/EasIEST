import xmlrpclib
import signal
from ...helpers import timeout_handler
from ...helpers import mydir
from ...helpers import top_dir
import json
import getpass
import paramiko


api_server = xmlrpclib.ServerProxy("https://www.planet-lab.org/PLCAPI/")
with open(top_dir+'config.json', 'r+') as f:
    config_data = json.load(f)


def create_auth():
    auth = {}
    auth['Username'] = config_data['planetlab_username']
    auth['AuthString'] = getpass.getpass()
    auth['AuthMethod'] = "password"
    return auth


# TODO cache me
def get_slice_id(auth, slice_name=config_data['planetlab_slice_name']):
    slices = api_server.GetSlices(auth, slice_name, ['name', 'slice_id'])
    return slices[0]['slice_id']


# TODO cache me
def refresh_nodes_list(auth):
    nodes = api_server.GetNodes(auth)
    with open(mydir()+'state/all_nodes.csv', 'w+') as f:
        json.dump(nodes, f)


def get_nodes_list(**kwargs):
    with open(mydir()+'state/all_nodes.csv', 'r+') as f:
        nodes = json.load(f)
    return nodes


def add_booted_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    new_booted_nodes = [n for n in nodes if n['boot_state'] == 'boot' and slice_id not in n['slice_ids']]
    nbn = list()
    states = set([n['boot_state'] for n in new_booted_nodes])
    print states
    for n in new_booted_nodes:
        nbn.append(n['node_id'])
        if 'allowed_val_sets' in kwargs:
            constraints = kwargs['allowed_val_sets']
            for c in constraints:
                if n[c] not in kwargs['allowed_val_sets'][c]:
                    nbn.pop()
                    break

    api_server.AddSliceToNodes(auth, slice_id, nbn)


def refresh_added_node_list(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    my_nodes = [n for n in nodes if slice_id in n['slice_ids']]
    with open(mydir()+'state/added_nodes.csv', 'w+') as f:
        json.dump(my_nodes, f)


def get_added_nodes(**kwargs):
    with open(mydir() + 'state/added_nodes.csv', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_slice_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    return [n for n in nodes if slice_id in n['slice_ids']]


def drop_dead_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list(auth)
    old_dead_nodes = [n for n in nodes if n['boot_state'] != 'boot' and slice_id in n['slice_ids']]
    api_server.DeleteSliceToNodes(auth, slice_id, old_dead_nodes)


def setup_python(auth, node_name):
    pass


def setup_golang():
    pass


def setup_node(auth, nodename, setup_method=setup_python, **kwargs):
    my_nodes = get_usable_nodes()
    usable_nodes = list()
    bad_nodes = list()
    for node in my_nodes:
        print node['hostname']
        try:
            client = paramiko.client.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(node['hostname'],
                    key_filename=config_data['planetlab_ssh_key'],
                           username=config_data['planetlab_slice_name'], timeout=3)
            setup_method(client=client, node=node, **kwargs)
            client.close()
            usable_nodes.append(node['hostname'])
        except Exception as e:
            bad_nodes.append((node['hostname'], str(e)))
    with open(mydir() + 'state/successful_setup_nodes.json', 'w+') as f:
        json.dump(usable_nodes, f)
    with open(mydir()+'state/failed_setup_nodes.json', 'w+') as f:
        json.dump(bad_nodes, f)


def has_mypython():
    pass


def has_mygolang():
    pass


def refresh_usable_nodes_list(**kwargs):
    """
    Get set of nodes with your slice that are actually responsive and meet some given set of requirements.

    :param kwargs: kwargs can include: 1) a function to run on an ssh client and node dict to check for
     requirements, deploy setup, etc

    writes output to state/usable_nodes.json and state/bad_nodes.json

    NOTE: although it is possible to use this function for experiment deployment, I recommend only using
     this method for establishing your list of currently usable nodes. It would be more readable to use
      a separate, dedicated function for experiment deployment, such as setup_node()
    """
    my_nodes = get_added_nodes()
    usable_nodes = list()
    bad_nodes = list()
    count = 0
    for node in my_nodes:
        print node['hostname']
        try:
            client = paramiko.client.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(node['hostname'],
                    key_filename=config_data['planetlab_ssh_key'],
                           username=config_data['planetlab_slice_name'], timeout=3)
            for k in kwargs:
                typestr = str(type(kwargs[k]))
                if 'function' in typestr or 'method' in typestr:
                    kwargs[k](client=client, node=node)
            client.close()
            usable_nodes.append(node)
        except Exception as e:
            bad_nodes.append((node, str(e)))
        if count % 20 == 0:
            with open(mydir() + 'state/usable_nodes.json', 'w+') as f:
                json.dump(usable_nodes, f)
        count += 1
    with open(mydir() + 'state/usable_nodes.json', 'w+') as f:
        json.dump(usable_nodes, f)
    with open(mydir()+'state/bad_nodes.json', 'w+') as f:
        json.dump(bad_nodes, f)


def get_usable_nodes():
    with open(mydir() + 'state/usable_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_bad_nodes():
    with open(mydir() + 'state/bad_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_ready_nodes():
    with open(mydir() + 'state/successful_setup_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_failed_setup_nodes():
    with open(mydir() + 'state/failed_setup_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def drop_bad_nodes(auth, unusable=True, failed_setup=True, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = list()
    if unusable:
        nodes += get_bad_nodes()
    if failed_setup:
        nodes += get_failed_setup_nodes()
    api_server.DeleteSliceToNodes(auth, slice_id, nodes)
