import xmlrpclib
import signal
import sys, traceback
from ...helpers import timeout_handler
from ...helpers import mydir
from ...helpers import top_dir
from ...helpers import format_dirpath
from ...helpers import terminal
from ...helpers import untar, make_tarfile
from ...helpers import isfile
import json
import getpass
import paramiko
import threading


##############################################################
#                     LOGGING SETUP
##############################################################
import logging.config
import logging

# load logger config file and create logger
logging.config.fileConfig(top_dir+'logging.conf',
        disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.debug("top directory level set to: "+top_dir)


##############################################################
#                     CODE
##############################################################


api_server = xmlrpclib.ServerProxy("https://www.planet-lab.org/PLCAPI/")
with open(top_dir+'config.json', 'r+') as f:
    config_data = json.load(f)
state_data_path = format_dirpath(config_data['data_path']+"/state_data/planet_lab/")
tmp_path = format_dirpath(config_data['tmp_path'])
wan_name = config_data['wan_name']
local_user = config_data['local_user']


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
    with open(state_data_path+'all_nodes.csv', 'w+') as f:
        json.dump(nodes, f)


def get_nodes_list(**kwargs):
    with open(state_data_path+'all_nodes.csv', 'r+') as f:
        nodes = json.load(f)
    return nodes


def add_booted_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    new_booted_nodes = [n for n in nodes if n['boot_state'] == 'boot' and slice_id not in n['slice_ids']]
    nbn = list()
    states = set([n['boot_state'] for n in new_booted_nodes])
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
    with open(state_data_path+'added_nodes.csv', 'w+') as f:
        json.dump(my_nodes, f)


def get_added_nodes(**kwargs):
    with open(state_data_path+'added_nodes.csv', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_slice_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    return [n for n in nodes if slice_id in n['slice_ids']]


def drop_dead_nodes(auth, **kwargs):
    slice_id = get_slice_id(auth, **kwargs)
    nodes = get_nodes_list()
    old_dead_nodes = [n for n in nodes if n['boot_state'] != 'boot' and slice_id in n['slice_ids']]
    logger.debug("# old dead nodes: "+str(len(old_dead_nodes)))
    api_server.DeleteSliceToNodes(auth, slice_id, old_dead_nodes)


def setup_python(client, **kwargs):
    '''
    Installs Python 2.7.12, which can be called with "python2.7" afterwards
    '''
    # check first to see if we've already installed it (to save time)
    stdin, stdout, stderr = client.exec_command("python2.7 -V", timeout=10)
    stdoutdata = stdout.read()
    stdoutdata += stderr.read()
    logger.debug("checking for python installation...")
    if "2.7.12" in stdoutdata:
        logger.debug("already installed, moving on...")
        return
    logger.debug("installing python...")
    steps = ["sudo rm -r ./*; mkdir local; cd local; wget \
            https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz; \
            sudo rm Python-2.7.12/ -r; tar -xzvf Python-2.7.12.tgz; \
            sudo yum -y install gcc-c++ --nogpgcheck; \
            sudo yum -y install vim --nogpgcheck; \
            sudo yum -y install openssl-devel --nogpgcheck; \
            cd Python-2.7.12; ./configure --prefix=$HOME/local \
            --with-zlib-dir=/usr/local/lib --with-ensurepip=yes --enable-shared; \
            sudo yum -y install make --nogpgcheck; make; make install; \
            export PATH=$HOME/local/bin:$PATH; \
            export LD_LIBRARY_PATH=$HOME/local/lib:$LD_LIBRARY_PATH; \
            echo \"export PATH=$HOME/local/bin:$PATH\" >> ~/.bashrc; \
            echo \"export LD_LIBRARY_PATH=$HOME/local/lib:$LD_LIBRARY_PATH\" >> ~/.bashrc; \
            python2.7 -m pip install --upgrade pip; \
            python2.7 -m pip install --upgrade setuptools"]
    for cmd in steps:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=3600)
        tmp = stdout.read()
        tmp += stderr.read()
        logger.debug("stdout/err: "+tmp)


def setup_curl(client, **kwargs):
    '''
    NOTE: assumes python 2.7 has already been set up
    '''
    steps = ["sudo yum -y install curl-devel --nogpgcheck; \
            python2.7 -m pip install pycurl==7.18.2"]
    for cmd in steps:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
        _ = stdout.read()


def setup_sudoers(client, **kwargs):
    '''
    NOTE: assumes python 2.7 has already been set up
    '''
    steps = ["sudo sed -i 's/ env_reset/\ !env_reset/g' /etc/sudoers"]
    for cmd in steps:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
        _ = stdout.read()


def execute_cmd(client, cmd, longouts=False, timeout=60, **kwargs):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    tmp = stdout.read()
    tmp += stderr.read()
    logger.debug("stdout/err: "+tmp)
    if len(tmp) > 50 and not longouts:
        raise RuntimeError


def push_dir(client, node_hostname, pushdir, local_overwrite_tar=False,
        remote_overwrite=False, destdir="", **kwargs):
    '''
    # uploads a file to a node via scp
    '''
    if pushdir[-1] == "/":
        pushdir = pushdir[:-1]
    filename = pushdir.split("/")[-1] + ".tar.gz"


    filepath = tmp_path+filename
    # save work here if it's already been tarballed
    if local_overwrite_tar or not isfile(filepath):
        logger.debug("overwriting "+filepath)
        make_tarfile(filepath, pushdir)
    stdin, stdout, stderr = client.exec_command("ls", timeout=20)
    stdoutdata = stdout.read()
    stdoutdata += stderr.read()
    # save work if it's already been uploaded
    if filename not in stdoutdata or remote_overwrite:
        tmp = terminal(" ".join(['scp', '-i', config_data['planetlab_ssh_key'], filepath,
            config_data['planetlab_slice_name']+'@'+node_hostname+':'+destdir]))
        logger.debug("\n".join(tmp))
    stdin, stdout, stderr = client.exec_command("tar -xzf "+filename, timeout=120)
    tmp = stdout.read()
    logger.debug(tmp)


def push_file(client, node_hostname, pushfile, local_overwrite_tar=False,
        remote_overwrite=False, destdir="", **kwargs):
    '''
    # uploads a file to a node via scp
    '''
    stdin, stdout, stderr = client.exec_command("ls "+destdir, timeout=20)
    stdoutdata = stdout.read()
    stdoutdata += stderr.read()
    # save work if it's already been uploaded
    if pushfile not in stdoutdata or remote_overwrite:
        tmp = terminal(" ".join(['scp', '-i', config_data['planetlab_ssh_key'],
            pushfile,
            config_data['planetlab_slice_name']+'@'+node_hostname+':'+destdir]))
        logger.debug("\n".join(tmp))
    stdin, stdout, stderr = client.exec_command("tar -xzf "+pushfile, timeout=120)
    tmp = stdout.read()
    logger.debug(tmp)


def setup_golang():
    pass


def command_node(hostname, cmd, longouts=True, **kwargs):
    logger.debug("connecting..."+hostname)
    client = None
    success = False
    try:
        client = connect_client(hostname)
        logger.debug("connected!")
        execute_cmd(client=client, cmd=cmd, node_hostname=hostname,
                longouts=longouts, **kwargs)
        success = True
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                              limit=2, file=sys.stdout)
        logger.error(str(e)+" Failed to command "+hostname)
    finally:
        if client is not None:
            client.close()
    return success


def get_node_ip(hostname, **kwargs):
    logger.debug("connecting..."+hostname)
    client = None
    ip = None
    try:
        client = connect_client(hostname)
        logger.debug("connected!")
        ip = client.get_transport().getpeername()[0]
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                              limit=2, file=sys.stdout)
        logger.error(str(e)+" Failed to get IP from  "+hostname)
    finally:
        if client is not None:
            client.close()
    return ip


def worker_thread(node, setup_methods,  **kwargs):
    logger.debug("connecting..."+node['hostname'])
    client = None
    try:
        client = connect_client(node['hostname'])
        logger.debug("connected!")
        for i, m in enumerate(setup_methods):
            logger.debug("calling"+str(i))
            m(client=client, node_hostname=node['hostname'], **kwargs)
        tlock.acquire()
        usable_nodes.append(node['hostname'])
        tlock.release()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                              limit=2, file=sys.stdout)
        logger.error(str(e))
        tlock.acquire()
        bad_nodes.append((node['hostname'], str(e)))
        tlock.release()
        logger.error("failed to set up "+node['hostname'])
    finally:
        if client is not None:
            client.close()
        tevent.set()


def setup_nodes(auth, setup_methods=[setup_python], max_nodes=0,
        max_threads=5, **kwargs):
    my_nodes = get_usable_nodes()
    global usable_nodes
    usable_nodes = list()
    global bad_nodes
    bad_nodes = list()
    global tlock
    tlock = threading.Lock()
    global tevent
    tevent = threading.Event()
    for node in my_nodes:
        if max_nodes > 0 and len(usable_nodes) >= max_nodes:
            break
        if threading.active_count() >= max_threads:
            tevent.wait()
            tevent.clear()
        thread = threading.Thread(target=worker_thread, args=(node,
            setup_methods), kwargs=kwargs)
        thread.daemon = True
        thread.start()

    with open(state_data_path+'successful_setup_nodes.json', 'w+') as f:
        json.dump(usable_nodes, f)
    with open(state_data_path+'failed_setup_nodes.json', 'w+') as f:
        json.dump(bad_nodes, f)


def has_mypython():
    pass


def has_mygolang():
    pass


def connect_client(nodename):
    key = paramiko.RSAKey.from_private_key_file(config_data['planetlab_ssh_key'])
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=nodename,
    username=config_data['planetlab_slice_name'], pkey=key, timeout=5)
    return client


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
        logger.debug("checking " +node['hostname'])
        try:
            client = connect_client(node['hostname'])
            client.exec_command("ls")
            usable_nodes.append(node)
        except Exception as e:
            bad_nodes.append((node, str(e)))
        finally:
            try:
                client.close()
            except:
                pass
        if count % 20 == 0:
            with open(state_data_path+'usable_nodes.json', 'w+') as f:
                json.dump(usable_nodes, f)
        count += 1
    with open(state_data_path+'usable_nodes.json', 'w+') as f:
        json.dump(usable_nodes, f)
    with open(state_data_path+'bad_nodes.json', 'w+') as f:
        json.dump(bad_nodes, f)


def get_usable_nodes():
    with open(state_data_path+'usable_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_nodes():
    nodes = list()
    with open(state_data_path + "successful_setup_nodes.json", 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_bad_nodes():
    with open(state_data_path+'bad_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_ready_nodes():
    with open(state_data_path+'successful_setup_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def get_failed_setup_nodes():
    with open(state_data_path+'failed_setup_nodes.json', 'r+') as f:
        nodes = json.load(f)
    return nodes


def drop_bad_nodes(auth, unusable=True, failed_setup=True, **kwargs):
    # TODO fix this?
    slice_id = get_slice_id(auth, **kwargs)
    nodes = list()
    if unusable:
        nodes += get_bad_nodes()
    if failed_setup:
        nodes += get_failed_setup_nodes()
    api_server.DeleteSliceToNodes(auth, slice_id, nodes)
