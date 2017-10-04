from IPy import IP
from geopy.distance import vincenty
import reverse_geocoder



class Location:
    """base class for a client's location"""

    # use geocoding to determine (as needed) a missing country attribute using other attributes (e.g. coordinates)
    infer_country = True
    # use geocoding to determine (as needed) a missing coordinates attribute using other attributes (e.g. country)
    infer_coordinates = False

    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def set_ipv4(self, ipv4):
        self.ipv4 = IP(ipv4)

    def set_ipv6(self, ipv6):
        self.ipv6 = IP(ipv6)

    def get_ipv4_subnet(self, masklen):
        return IP(str(self.ipv4)+'/'+str(masklen))

    def get_ipv6_subnet(self, masklen):
        return IP(str(self.ipv6) + '/' + str(masklen))

    def get_country(self):
        if not hasattr(self, 'country') and self.infer_country:
            if hasattr(self, 'coordinates'):
                country = reverse_geocoder.search(self.coordinates)[0]['cc']
                if type(country) is not str or len(country) != 2:
                    raise KeyError("'country' has not been defined for this location")
        elif hasattr(self, 'country'):
            return self.country

    def get_coordinates(self):
        # TODO
        pass


class Client:
    """base class for a client that will perform measurements"""
    def __init__(self, platform, location):
        self.platform = platform
        self.location = location


class TargetLocation:
    """class for describing the set of required location constraints for client selection"""

    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def set_coordinate_circle(self, coordinates, radius):
        if type(coordinates) is not tuple or type(radius) is not float:
            raise ValueError("expected parameters format: (lat, long) (tuple(float, float)), kilometers radius (float)")
        self.coordinate_circle = {'coordinates': coordinates, 'radius': radius}

    def set_country(self, country):
        if len(country) == 2 and country.isupper():
            self.country = country
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
            return vincenty(location.coordinates, coordinates).kilometers <= radius
        elif hasattr(location, 'country'):
            # TODO
            pass



    def __contains__(self, location):
        if type(location) is Client:
            location = location.location
        elif type(location) is not Location:
            raise ValueError("expected input type to be Client or Location")

        # we only need to check the constraints that have actually been set for this target location
        for area in vars(self):
            if hasattr(self, area+"_contains"):
                if not getattr(self, area+"_contains")(location):
                    return False
            elif hasattr(location, area):
                if getattr(location, area) != getattr(self, area):
                    return False

    def set(self, member, val):
        if hasattr(self, "set_"+member):
            getattr(self, "set_"+member)(val)
        else:
            setattr(self, member, val)


class TargetClientGroup:
    def __init__(self, target_location=None, target_quantity=None, platforms=None, **kwargs):
        self.target_location = target_location
        self.target_quantity = target_quantity
        self.platforms = platforms
        for k in kwargs:
            setattr(self, k, kwargs[k])


class ClientGroup:
    """base class for a group of clients that will perform measurements"""
    def __init__(self):
        self.clients = None