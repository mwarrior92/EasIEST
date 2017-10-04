from IPy import IP


class Location:
    """base class for a client's location"""
    def __init__(self, ipv4=None, ipv6=None, asn=None, coordinates=None, **kwargs):
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.asn = asn # autonomous system number
        self.coordinates = coordinates
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def set_ipv4(self, ipv4):
        if type(ipv4) is IP:
            self.ipv4 = ipv4
        else:
            self.ipv4 = IP(ipv4)

    def set_ipv6(self, ipv6):
        if type(ipv6) is IP:
            self.ipv6 = ipv6
        else:
            self.ipv6 = IP(ipv6)

    def get_ipv4_subnet(self, masklen):
        return IP(str(self.ipv4)+'/'+str(masklen))

    def get_ipv6_subnet(self, masklen):
        return IP(str(self.ipv6) + '/' + str(masklen))


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
            raise ValueError("expected parameters format: (lat, long) (tuple), radius (float)")
        self.coordinate_circle = {'coordinates': coordinates, 'radius': radius}

    def set_country(self, country):
        if len(country) == 2 and country.isupper():
            self.country = country
        else:
            # TODO: should automate this to pull country code list from a file and do conversions for other formats
            raise ValueError("expected capitalized, 2 char country code - for example, 'US', 'FR', etc")

    def set_ipv4_subnet(self, subnet):
        if type(subnet) is IP:
            self.ipv4_subnet = subnet
        else:
            self.ipv4_subnet = IP(subnet, make_net=True)

    def set_ipv6_subnet(self, subnet):
        if type(subnet) is IP:
            self.ipv6_subnet = subnet
        else:
            self.ipv6_subnet = IP(subnet, make_net=True)

    def __contains__(self, location):
        if type(location) is Client:
            location = location.location
        elif type(location) is not Location:
            raise ValueError("expected input type to be Client or Location")

        # we only need to check the constraints that have actually been set for this target location
        for check in vars(self):
            if hasattr(self, "contains_"+check):
                if not getattr(self, "contains_"+check)(location):
                    return False
            elif hasattr(location, check):
                if getattr(location, check) != getattr(self, check):
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