class Location:
    """base class for a client's location"""
    def __init__(self):
        self.ipv4 = None
        self.ipv6 = None
        self.asn = None # autonomous system number
        self.owners = None # ISP name, university name, etc
        self.coordinates = None

    def set_ipv4(self, ipv4):
        pass

    def set_ipv6(self, ipv6):
        pass

    def set_asn(self, asn):
        pass

    def set_owners(self, owner):
        pass

    def set_coordinates(self, latitude, longitude):
        pass

    def get_ipv4_subnet(self, mask):
        pass

    def get_ipv6_subnet(self, mask):
        pass

    def in_ipv4_subnet(self, subnet):
        pass

    def in_ipv6_subnet(self, subnet):
        pass

    def in_coordinate_range(self, coord_range):
        pass


class Client:
    """base class for a client that will perform measurements"""
    def __init__(self):
        self.platform = None
        self.location = None


class ClientGroup:
    """base class for a group of clients that will perform measurements"""
    def __init__(self):
        self.clients = None
