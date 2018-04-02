from IPy import IP
from geopy.distance import vincenty
from geopy.geocoders import Nominatim
from helpers import Extendable
from helpers import asn_lookup
from collections import defaultdict
import random
import platform_libs


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
            self.set(k, kwargs[k])

    def set_ipv4(self, ipv4):
        self.ipv4 = IP(ipv4)

    def set_ipv6(self, ipv6):
        self.ipv6 = IP(ipv6)

    def get_ipv4_subnet(self, masklen):
        return IP(str(self.get('ipv4'))+'/'+str(masklen))

    def get_ipv6_subnet(self, masklen):
        return IP(str(self.get('ipv6')) + '/' + str(masklen))

    def get_country_code(self):
        if hasattr(self, 'country_code'):
            return self.country_code
        elif self.infer_country_code:
            if hasattr(self, 'coordinates'):
                geolocator = Nominatim()
                loc = geolocator.reverse(self.get('coordinates'))
                country = loc.raw['address']['country_code']
                if type(country) is str and len(country) == 2:
                    country = country.upper()
                    self.set('country_code', country)
                    self.inferences.append(('country_code', country))
                    return country
            # throw an error if we don't have any way to get the country
            raise KeyError("member 'country' has not been defined for this location")
        else:
            # throw an error if we don't have any way to get the country
            raise KeyError("member 'country' has not been defined for this location")

    def get_coordinates(self):
        if hasattr(self, 'coordinates'):
            return self.coordinates
        elif self.infer_coordinates:
            if hasattr(self, 'country_code'):
                geolocator = Nominatim()
                loc = geolocator.geocode(self.get('country_code'))
                coordinates = (loc.latitude, loc.longitude)
                self.set('coordinates', coordinates)
                self.inferences.append(('coordinates', coordinates))
                return coordinates
            # throw an error if we don't have any way to get the coordinates
            raise KeyError("member 'coordinates' has not been defined for this location")
        else:
            # throw an error if we don't have any way to get the coordinates
            raise KeyError("member 'coordinates' has not been defined for this location")

    def get_asn_v4(self):
        if hasattr(self, 'asn_v4'):
            return self.asn_v4
        elif self.infer_asn:
            if hasattr(self, 'ipv4'):
                asn = asn_lookup(str(self.get('ipv4')))
                self.set('asn_v4', asn)
                self.inferences.append(('asn_v4', asn))
                return asn
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")
        else:
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")

    def get_asn_v6(self):
        if hasattr(self, 'asn_v6'):
            return self.asn_v6
        elif self.infer_asn:
            if hasattr(self, 'ipv6'):
                asn = asn_lookup(str(self.get('ipv6')))
                self.set('asn_v6', asn)
                self.inferences.append(('asn_v6', asn))
                return asn
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")
        else:
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")


class Client(Extendable):
    """base class for a client that will perform measurements"""
    def __init__(self, platform, location, **kwargs):
        self.platform = None
        self.location = None
        self.set("location", location)
        self.set("platform", platform)
        for k in kwargs:
            self.set(k, kwargs[k])

    def set_location(self, loc):
        if type(loc) is dict:
            self.location = Location(**loc)
        else:
            self.location = loc

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

    def set_ipv4_subnet(self, subnet):
        self.ipv4_subnet = IP(subnet, make_net=True)

    def set_ipv6_subnet(self, subnet):
        self.ipv6_subnet = IP(subnet, make_net=True)

    def ipv4_subnet_contains(self, location):
        return IP(location.ipv4) in self.ipv4_subnet

    def ipv6_subnet_contains(self, location):
        return IP(location.ipv6) in self.ipv6_subnet

    def coordinate_circle_contains(self, location):
        coordinates = self.coordinate_circle['coordinates']
        radius = self.coordinate_circle['radius']
        if hasattr(location, 'coordinates'):
            return vincenty(location.get_coordinates(), coordinates).kilometers <= radius

    def countries_contains(self, location):
        return location.get_country_code() in self.countries
<<<<<<< HEAD

    def v4_asns_contains(self, location):
        return location.get_v4_asn() in self.get('v4_asns')

=======

    def v4_asns_contains(self, location):
        return location.get_v4_asn() in self.get('v4_asns')

>>>>>>> a53601e7c4a3c585c3b6435788d2f92c03ded655
    def v6_asns_contains(self, location):
        return location.get_v6_asn() in self.get('v6_asns')

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

    def get_ClientGroup(self, platform):
        pl = getattr(platform_libs, platform)
        cg = getattr(pl, "get_TargetLocation_clients")(self.target_location)
<<<<<<< HEAD
        if self.target_quantity is not None:
            return ClientGroup(cg.random_sample(self.target_quantity))
        else:
            return cg
=======
        return ClientGroup(cg.random_sample(self.target_quantity))
>>>>>>> a53601e7c4a3c585c3b6435788d2f92c03ded655



class ClientGroup(Extendable):
    """base class for a group of clients that will perform measurements"""
    def __init__(self, clients=None):
        if type(clients) is list:
            self.clients = clients
        else:
            self.clients = list()

    def add_client(self, client):
        self.clients.append(client)

    def add_clients(self, clients):
        self.clients += clients

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

    def set_clients(self, clients):
        for c in clients:
            if type(c) is dict:
                self.add_client(Client(**c))
            else:
                self.add_client(c)

<<<<<<< HEAD
    def get_probe_ids(self):
        return [z.get('probe_id') for z in self.get('clients')]

    def intersection(self, cg2):
        ids1 = self.get('probe_ids')
        ids2 = cg2.get('probe_ids')
        overlap = set(ids1).intersection(ids2)
        return [z.get('probe_id') for z in self.get('clients') if z.get('probe_id') not in overlap]

=======
>>>>>>> a53601e7c4a3c585c3b6435788d2f92c03ded655

