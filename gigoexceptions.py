# exceptions for the gig-o-matic

class GigoException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
