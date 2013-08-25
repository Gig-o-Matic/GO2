#
# Make some test data
#

from band import *
from member import *
from assoc import *
from gig import *
from plan import *

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
    
    member1 = new_member(first_name='Aaron', last_name='Oppenheimer', email='test@example.com', nickname='test@example.com')
    member2 = new_member(first_name='Maury', last_name='Martin')
    
    new_association(slsaps,member1)
    new_association(slsaps,member2)

    membership = get_members_of_band(slsaps)
    for i in membership:
        print 'slsaps: {0}'.format(i.first_name)
    
    g1 = new_gig(band=slsaps, title="test gig 1")
    g2 = new_gig(band=slsaps, title="test gig 2")
    
    gigs = get_gigs_for_band(slsaps)
    for g in gigs:
        print 'gig: {0}'.format(g.title)
    
    new_plan(g1, member1, 1)
    new_plan(g1, member2, 2)
    
    plans=get_plans_for_gig(g1)
    for p in plans:
        m=p.member.get()
        print '{0} has a plan for gig {1}: {2}'.format(m.first_name, g1.title, p.value)