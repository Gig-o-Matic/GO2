#
# Make some test data
#

from band import *

def test_band():
    """make some test data"""
       
    def make_if_not_here(name):
        the_band=get_band(name)
        if the_band is None:
            the_band = Band(parent=band_key(), name=name, website="www.{0}.org".format(name))
            the_band.put()

    make_if_not_here("SLSAPS")
    make_if_not_here("EmperorNorton")
    make_if_not_here("EE")