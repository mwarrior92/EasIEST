from IPy import IP
from geopy.distance import vincenty
from geopy.geocoders import Nominatim
from helpers import Extendable
from helpers import asn_lookup


class Location(Extendable):
    """base class for a client's location"""

    # use geocoding to determine (as needed) a missing country attribute using other attributes (e.g. coordinates)
    infer_country = True
    # use geocoding to determine (as needed) a missing coordinates attribute using other attributes (e.g. country)
    infer_coordinates = False
    # use lookup to determine (as needed) a missing ASN attribute using other attributes (e.g. IPv4)
    infer_asn = True

    def __init__(self, **kwargs):
        if self.infer_country or self.infer_coordinates:
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

    def get_country(self):
        if not hasattr(self, 'country') and self.infer_country:
            if hasattr(self, 'coordinates'):
                geolocator = Nominatim()
                loc = geolocator.reverse(self.get('coordinates'))
                country = loc.raw['address']['country_code']
                if type(country) is str and len(country) == 2:
                    country = country.upper()
                    self.set('country', country)
                    self.inferences.append(('country', country))
                    return country
            # throw an error if we don't have any way to get the country
            raise KeyError("member 'country' has not been defined for this location")
        elif hasattr(self, 'country'):
            return self.country
        else:
            # throw an error if we don't have any way to get the country
            raise KeyError("member 'country' has not been defined for this location")

    def get_coordinates(self):
        if not hasattr(self, 'coordinates') and self.infer_coordinates:
            if hasattr(self, 'country'):
                geolocator = Nominatim()
                loc = geolocator.geocode(self.get('country'))
                coordinates = (loc.latitude, loc.longitude)
                self.set('coordinates', coordinates)
                self.inferences.append(('coordinates', coordinates))
                return coordinates
            # throw an error if we don't have any way to get the coordinates
            raise KeyError("member 'coordinates' has not been defined for this location")
        elif hasattr(self, 'coordinates'):
            return self.coordinates
        else:
            # throw an error if we don't have any way to get the coordinates
            raise KeyError("member 'coordinates' has not been defined for this location")

    def get_asn(self):
        if not hasattr(self, 'asn') and self.infer_asn:
            if hasattr(self, 'ipv4'):
                asn = asn_lookup(str(self.get('ipv4')))
                self.set('asn', asn)
                self.inferences.append(('asn', asn))
                return asn
            elif hasattr(self, 'ipv6'):
                asn = asn_lookup(str(self.get('ipv6')))
                self.set('asn', asn)
                self.inferences.append(('asn', asn))
                return asn
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")
        elif hasattr(self, 'asn'):
            return self.asn
        else:
            # throw an error if we don't have any way to get the ASN
            raise KeyError("member 'asn' has not been defined for this location")


class Client(Extendable):
    """base class for a client that will perform measurements"""
    def __init__(self, platform, location, **kwargs):
        self.platform = platform
        self.location = location
        for k in kwargs:
            setattr(self, k, kwargs[k])


class TargetLocation(Extendable):
    """class for describing the set of required location constraints for client selection"""

    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def set_coordinate_circle(self, coordinates, radius):
        if type(coordinates) is not tuple or type(radius) is not float:
            raise ValueError("expected parameters format: (lat, long) (tuple(float, float)), kilometers radius (float)")
        self.coordinate_circle = {'coordinates': coordinates, 'radius': radius}

    def set_countries(self, countries):
        self.countries = list()
        if type(countries) is not list or type(countries) is not tuple:
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
        return location.get_country() in self.countries

    def asns_contains(self, location):
        return location.get_asn() in self.get('asns')

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
    def __init__(self, target_location, target_quantity=None, platforms=None, **kwargs):
        self.target_location = target_location
        self.target_quantity = target_quantity
        self.platforms = platforms
        for k in kwargs:
            self.set(k, kwargs[k])

    def __contains__(self, client):
        target_location = self.get('target_location')
        platforms = self.get('platforms')
        if platforms is not None:
            if client.get['platform'] not in platforms:
                return False
        if client.location not in target_location:
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



class ClientGroup:
    """base class for a group of clients that will perform measurements"""
    def __init__(self):
        self.clients = None

    def split_by(self, feature):
        # TODO - out put subgroups e.g. grouped by country, etc
        pass

    @staticmethod
    def merge(*groups):
        # TODO - merge groups together
        pass