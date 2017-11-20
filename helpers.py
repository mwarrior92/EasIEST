import inspect
import os
import shutil
import logging.config
from ipwhois import IPWhois
import datetime

"""
NOTE: most of the helper functions are just to make main code less cluttered
"""

##############################################################
#                       PATH SETUP
##############################################################


def mydir():
    f = os.path.abspath(inspect.stack()[1][1])  # source [1]
    d = "/".join(f.split("/")[:-1]) + "/"
    return d


self_file = os.path.abspath(inspect.stack()[0][1]) # source [1]
top_dir = "/".join(self_file.split("/")[:-1])+"/"


##############################################################
#                     LOGGING SETUP
##############################################################

# load logger config file and create logger
logging.config.fileConfig(top_dir+'logging.conf',
        disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.debug("top directory level set to: "+top_dir)

##############################################################
#                        FILE I/O
##############################################################


def overwrite(path, content):
    """
    :param path: (str) path to file to be written to (including file name)
    :param content: (str) data to be written to file

    this is a simple wrapper to reduce 'w+' writes into clean one-liners
    """
    try:
        f = open(path, 'w+')
        try:
            f.write(content)
        finally:
            f.close()
    except IOError:
        logger.error("failed to overwrite "+path)
        return
    logger.debug("successfully overwrote "+path)


def append_file(path, content):
    """
    :param path: (str) path to file to be written to (including file name)
    :param content: (str) data to be written to file

    this is a simple wrapper to reduce 'a+' writes into clean one-liners
    """

    try:
        f = open(path, 'a+')
        try:
            f.write(content)
        finally:
            f.close()
    except IOError:
        logger.error("failed to append to "+path)
        return
    logger.debug("successfully appended to "+path)


def format_dirpath(path):
    """
    :param path: (str) a path to a dir in a filesystem; assumes path uses '/' as
    dir delimitter
    :return: (str) a properly formatted, absolute path string

    This 1) removes relative '..' items from the path, 2) removes redundant '/'
    from the path, 3) creates any non-existant directories in the path, 4) ends
    thee path with '/'

    NOTE: this will build an ABSOLUTE path, CREATING any non-existant
    directories along the way as needed. ONLY use this when you KNOW the path is
    EXACTLY what you want/need it to be.
    """
    dirs = path.split('/')
    path = '/'
    if dirs[0] != "":
        raise ValueError('relative path not allowed')
    for d in dirs:
        # account for empty strings from split
        if d == '..':
            path = '/'.join(path.split('/')[:-2])+'/'
        elif d != '':
            path = path + d + '/'
        else:
            continue
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            logger.error('OSError creating file path for '+path)
    logger.debug("corrected path: "+path)
    return path


def listfiles(parentdir, prefix="", containing="", suffix=""):
    """
    :param parentdir: (str) the directory from which you would like the files listed
    :param prefix: (str) leading characters to match in returned file names
    :param containing: (str) substring to match in returned file names
    :param suffix: (str) trailing characters to match in returned file names
    :return: (list(str)) list of file names from parentdir that meet the param
    constraints
    """
    # return list of file names in parentdir;
    # setting fullpath to True will give filenames with the direct/full path as
    # a prefix
    for root, dirs, files in os.walk(parentdir):
        outlist = list()
        for f in files:
            if f.startswith(prefix) and containing in f and f.endswith(suffix):
                outlist.append(f)
        return outlist


def remove(fname):
    """
    :param fname: (str) the name of the file to be removed

    removes (deletes) the file, 'fname'

    NOTE: also accepts directories and wildcards
    NOTE: directories must end in '/'
    """
    try:
        if fname[-1] == '*' or fname[-1] == '/':
            shutil.rmtree(fname)
        else:
            os.remove(fname)
    except OSError as e:
        logger.error('OSError removing '+fname+"; "+str(e))
        return
    logger.debug("Successfully removed "+fname)

##############################################################
#                   GENERIC BASE CLASSES
##############################################################


class Extendable:
    def get(self, member):
        """
        :param member: (str) name of member whose value should be returned
        :return:
        """
        if hasattr(self, "get_"+member):
            return getattr(self, "get_"+member)()
        else:
            return vars(self)[member]

    def set(self, member_name, val):
        """

        :param member:
        :param val:
        :return:
        """
        if hasattr(self, "set_"+member_name):
            getattr(self, "set_"+member_name)(val)
        else:
            setattr(self, member_name, val)

##############################################################
#               NETWORKING CLASSES AND METHODS
##############################################################


def whois_lookup(ipstr, **kwargs):
    """

    :param ipstr:
    :param kwargs:
    :return: (dict) result of IPWhois lookup

     NOTE: this should be wrapped by a decorator to implement caching
     for faster/more reliable lookups
    """
    obj = IPWhois(ipstr)
    return obj.lookup_rdap(**kwargs)


def asn_lookup(ipstr, **kwargs):
    """

    :param ipstr:
    :param kwargs:
    :return:
    """
    results = whois_lookup(ipstr, **kwargs)
    if results is not None:
        return int(results['asn'])
    else:
        return None


def cidr_lookup(ipstr, **kwargs):
    """

    :param ipstr:
    :param kwargs:
    :return:
    """
    results = whois_lookup(ipstr, **kwargs)
    if results is not None:
        return int(results['network']['cidr'])
    else:
        return None


class TimeoutError(BaseException):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("timeout")


def datestr(dt):
    return dt.strftime("%Yy%mm%dd%Hh")


def timestr(dt):
    return str((dt - datetime.datetime(1970, 1, 1)).total_seconds())

