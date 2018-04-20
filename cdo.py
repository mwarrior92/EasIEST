from IPy import IP
from geopy.distance import vincenty
from geopy.geocoders import Nominatim
from helpers import Extendable
from helpers import asn_lookup
from collections import defaultdict
import random
import platform_libs
from numpy import ceil


class Location(Extendable):
    """base class for a client's location"""

    # use geocoding to determine (as needed) a missing country attribute using other attributes (e.g. coordinates)
    infer_country_code = True
    # use geocoding to determine (as needed) a missing coordinates attribute using other attributes (e.g. country)
    infer_coordinates = False
    # use lookup to determine (as needed) a missing ASN attribute using other attributes (e.g. IPv4)
    infer_asn = True

    def __init__(self, **kwargs):
        self.inferences = list()
        for k in kwargs:
            # self.set(k, kwargs[k])
            try:
                setattr(self, k, kwargs[k])
            except Exception as e:
                print k
                raise e

    @property
    def ipv4(self):
        if hasattr(self, '_ipv4'):
            return self._ipv4
        else:
            return None

    @ipv4.setter
    def ipv4(self, ipv4):
        self._ipv4 = IP(ipv4)

    @property
    def ipv6(self):
        if hasattr(self, '_ipv6'):
            return self._ipv6
        else:
            return None

    @ipv6.setter
    def ipv6(self, ipv6):
        self._ipv6 = IP(ipv6)

    def get_ipv4_subnet(self, masklen):
        return IP(str(self.ipv4)+'/'+str(masklen))

    def get_ipv6_subnet(self, masklen):
        return IP(str(self.ipv6) + '/' + str(masklen))

    @property
    def country_code(self):
        if hasattr(self, '_country_code'):
            return self._country_code
        elif self.infer_country_code:
            if hasattr(self, '_coordinates'):
                geolocator = Nominatim()
                loc = geolocator.reverse(self.coordinates)
                country = loc.raw['address']['country_code']
                if type(country) is str and len(country) == 2:
                    country = country.upper()
                    self._country_code = country
                    self.inferences.append(('country_code', country))
                    return country
            # throw an error if we don't have any way to get the country
            return None
        else:
            return None

    @country_code.setter
    def country_code(self, val):
        self._country_code = val

    @property
    def country(self):
        return self.country_code

    @country.setter
    def country(self, val):
        self.country_code = val

    @property
    def coordinates(self):
        if hasattr(self, '_coordinates'):
            return self._coordinates
        elif self.infer_coordinates:
            if hasattr(self, '_country_code'):
                geolocator = Nominatim()
                loc = geolocator.geocode(self.country_code)
                coordinates = (loc.latitude, loc.longitude)
                self._coordinates = coordinates
                self.inferences.append(('coordinates', coordinates))
                return coordinates
            # throw an error if we don't have any way to get the coordinates
            return None
        else:
            return None

    @coordinates.setter
    def coordinates(self, val):
        self._coordinates = val

    @property
    def asn_v4(self):
        if hasattr(self, '_asn_v4'):
            return self._asn_v4
        elif self.infer_asn:
            if self.ipv4 is not None:
                asn = asn_lookup(str(self.ipv4))
                self._asn_v4 = asn
                self.inferences.append(('asn_v4', asn))
                return asn
            # throw an error if we don't have any way to get the ASN
            return None
        else:
            # throw an error if we don't have any way to get the ASN
            return None

    @asn_v4.setter
    def asn_v4(self, val):
        self._asn_v4 = val

    @property
    def asn_v6(self):
        if hasattr(self, '_asn_v6'):
            return self._asn_v6
        elif self.infer_asn:
            if self.ipv6 is not None:
                asn = asn_lookup(str(self.ipv6))
                self._asn_v6 = asn
                self.inferences.append(('asn_v6', asn))
                return asn
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")
        else:
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")

    @asn_v6.setter
    def asn_v6(self, val):
        self._asn_v6 = val


class Client(Extendable):
    """base class for a client that will perform measurements"""
    def __init__(self, platform, location, **kwargs):
        self.location = location
        self.platform = platform
        for k in kwargs:
            self.set(k, kwargs[k])

    def __getattribute__(self, k):
        try:
            return object.__getattribute__(self, k)
        except AttributeError as initial:
            try:
                return object.__getattribute__(self.location, k)
            except AttributeError:
                raise initial

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, loc):
        if type(loc) is dict:
            self._location = Location(**loc)
        else:
            self._location = loc

    def get(self, member):
        """
                :param member: (str) name of member whose value should be returned
                :return:
                """
        if hasattr(self, "get_" + member):
            return getattr(self, "get_" + member)()
        elif hasattr(self, member):
            return getattr(self, member)
        else:
            return self.location.get(member)  # added this to avoid abstraction confusion


class TargetLocation(Extendable):
    """class for describing the set of required location constraints for client selection"""

    def __init__(self, **kwargs):
        """

        :param kwargs: coordinate_circle, countries, ipv[4/6]_subnet, v[4/6]_asns
        """
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def set_coordinate_circle(self, coordinates, radius):
        if type(coordinates) is not tuple or type(radius) is not float:
            raise ValueError("expected parameters format: (lat, long) (tuple(float, float)), kilometers radius (float)")
        self.coordinate_circle = {'coordinates': coordinates, 'radius': radius}

    def set_countries(self, countries):
        self.countries = list()
        if not hasattr(countries, '__iter__'):
            raise ValueError("expected list of capitalized, 2 char country codes")
        for country in countries:
            if len(country) == 2 and country.isupper():
                self.countries.append(country)
            else:
                # TODO: should automate this to pull country code list from a file and do conversions for other formats
                raise ValueError("expected capitalized, 2 char country code - for example, 'US', 'FR', etc")

    @property
    def ipv4_subnet(self):
        return self._ipv4_subnet

    @ipv4_subnet.setter
    def ipv4_subnet(self, subnet):
        self._ipv4_subnet = IP(subnet, make_net=True)

    @property
    def ipv6_subnet(self):
        return self._ipv6_subnet

    @ipv6_subnet.setter
    def ipv6_subnet(self, subnet):
        self._ipv6_subnet = IP(subnet, make_net=True)

    def ipv4_subnet_contains(self, location):
        return IP(location.ipv4) in self.ipv4_subnet

    def ipv6_subnet_contains(self, location):
        return IP(location.ipv6) in self.ipv6_subnet

    def coordinate_circle_contains(self, location):
        coordinates = self.coordinate_circle['coordinates']
        radius = self.coordinate_circle['radius']
        if location.coordinates is not None:
            return vincenty(location.coordinates, coordinates).kilometers <= radius

    def countries_contains(self, location):
        return location.get_country_code() in self.countries

    def v4_asns_contains(self, location):
        return location.get_v4_asn() in self.v4_asns

    def v6_asns_contains(self, location):
        return location.get_v6_asn() in self.v6_asns

    def __contains__(self, location):
        if type(location) is Client:
            location = location.location
        elif type(location) is not Location:
            raise ValueError("expected input type to be Client or Location")

        # we only need to check the constraints that have actually been set for this target location
        for constraint in vars(self):  # dynamic check
            if hasattr(self, constraint+"_contains"):
                try:
                    if not getattr(self, constraint+"_contains")(location):
                        return False
                except KeyError:
                    return False
            elif hasattr(location, constraint):
                if isinstance(getattr(self, constraint), type(getattr(location, constraint))):
                    if getattr(location, constraint) != getattr(self, constraint):
                        return False
                elif hasattr(getattr(self, constraint), '__contains__'):
                    if getattr(location, constraint) not in getattr(self, constraint):
                        return False
                else:
                    return False
            else:
                return False
        return True


class TargetClientGroup(Extendable):
    def __init__(self, target_location, target_quantity=None, **kwargs):
        self.target_location = target_location
        self.target_quantity = target_quantity
        for k in kwargs:
            self.set(k, kwargs[k])

    def __contains__(self, client):
        if client.location not in self.target_location:
            return False

        # we only need to check the constraints that have actually been set for this target location
        for constraint in vars(self):  # dynamic check
            if hasattr(self, constraint+"_contains"):
                try:
                    if not getattr(self, constraint+"_contains")(client):
                        return False
                except KeyError:
                    return False
            elif hasattr(client, constraint):
                if isinstance(getattr(self, constraint), type(getattr(client, constraint))):
                    if getattr(client, constraint) != getattr(self, constraint):
                        return False
                elif hasattr(getattr(self, constraint), '__contains__'):
                    if getattr(client, constraint) not in getattr(self, constraint):
                        return False
                else:
                    return False
            else:
                return False
        return True

    def get_ClientGroup(self, platform, **kwargs):
        pl = getattr(platform_libs, platform)
        cg = getattr(pl, "get_TargetLocation_clients")(self.target_location, **kwargs)
        if self.target_quantity is not None:
            if 'groupby' in kwargs:
                groupby = kwargs['groupby']
                vals = [z.get(kwargs['groupby']) for z in cg.clients]
                if 'groupsize' in kwargs:
                    groupsize = kwargs['groupsize']
                else:
                    groupsize = int(ceil(float(self.target_quantity) / float(len(vals))))
                clients = list()
                i = 0
                counts = defaultdict(int)
                groups = defaultdict(list)
                for c in cg.clients:
                    groups[c.get(groupby)].append(c)
                keys = sorted(groups.keys(), key=lambda z: len(groups[z]), reverse=True)
                for k in keys:
                    for c in groups[k]:
                        if counts[k] < groupsize and not any([c.ipv4 == z.ipv4 for z in clients]):
                            clients.append(c)
                            counts[c.get(groupby)] += 1
                        elif counts[k] >= groupsize:
                            break
                    if len(clients) > self.target_quantity - 1:
                        break
                return ClientGroup(random.sample(clients, self.target_quantity))

            else:
                return ClientGroup(cg.random_sample(self.target_quantity))
        else:
            return cg



class ClientGroup(Extendable):
    """base class for a group of clients that will perform measurements"""
    def __init__(self, clients=None):
        if type(clients) is list:
            self._clients = clients
        else:
            self._clients = list()

    def add_client(self, client):
        self._clients.append(client)

    def add_clients(self, clients):
        self._clients += clients

    def split(self, check_method):
        """
        outputs a dictionary of smaller ClientGroups, grouped by the output of check_method
        :param check_method: a method whose input is a Client and whose output is a corresponding
         group label for that client
        :return:
        """
        outgroups = defaultdict(ClientGroup)
        for client in self.clients:
            outgroups[check_method(client)].add_client(client)
        return outgroups

    @staticmethod
    def merge(*groups):
        cg = ClientGroup()
        for group in groups:
            cg.add_clients(group.clients)
        return cg

    def random_sample(self, sample_size):
        return random.sample(self.clients, sample_size)

    def __iter__(self):
        for client in self.clients:
            yield client

    @property
    def clients(self):
        return self._clients

    @clients.setter
    def clients(self, clients):
        for c in clients:
            if type(c) is dict:
                self.add_client(Client(**c))
            else:
                self.add_client(c)

    @property
    def probe_ids(self):
        return [z.probe_id for z in self.clients]

    @probe_ids.setter
    def probe_ids(self, val):
        self._probe_ids = val

    def intersection(self, cg2):
        ids1 = self.probe_ids
        ids2 = cg2.probe_ids
        overlap = set(ids1).intersection(ids2)
        return [z.probe_id for z in self.clients if z.probe_id not in overlap]

