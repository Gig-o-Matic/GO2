#
# Make some test data
#

from band import *
from member import *
from assoc import *

def test_band():
    """make some test data"""
       
    def make_if_not_here(name):
        the_band=get_band_from_name(name)
        if the_band is None:
            the_band=new_band(name=name, website="www.{0}.org".format(name))
        return the_band

    slsaps=make_if_not_here("SLSAPS")
    make_if_not_here("EmperorNorton")
    make_if_not_here("EE")
    
    member1 = new_member(first_name='Aaron', last_name='Oppenheimer')
    member2 = new_member(first_name='Maury', last_name='Martin')
    
    new_association(slsaps,member1)
    new_association(slsaps,member2)

    membership = get_members_of_band(slsaps)
    for i in membership:
        print 'slsaps: {0}'.format(i.first_name)
    
