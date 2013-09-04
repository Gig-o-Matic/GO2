#
# Make some test data
#

from google.appengine.ext import ndb

import band
import member
import assoc
import gig
import plan

import datetime

def test_band():
    """make some test data"""

    # delete the data if there is any
    # Clear datastore entities
    for model in [band.Band, member.Member, assoc.Assoc, gig.Gig, plan.Plan]:
        ndb.delete_multi(model.query().fetch(999999, keys_only=True))
 
    # Clear memcache
    ndb.get_context().clear_cache()      


    def make_if_not_here(name,admin):
        the_band=band.get_band_from_name(name)
        if the_band is None:
            the_band=band.new_band(name=name, admin=admin)
        return the_band
    
    member1 = member.new_member(name='Aaron', email='aoppenheimer@gmail.com', nickname='aoppenheimer', role=1)
    member2 = member.new_member(name='Maury', nickname='mmartin')
    member3 = member.new_member(name='Kate', email='katervw@gmail.com', nickname='katervw')
    
    slsaps=make_if_not_here("SLSAPS",member1)
    make_if_not_here("EmperorNorton",member1)
    ee=make_if_not_here("EE",member1)

    assoc.new_association(slsaps,member1)
    assoc.new_association(ee,member1)
    assoc.new_association(slsaps,member2)
    assoc.new_association(slsaps,member3)

    membership = band.get_members_of_band(slsaps)
    for i in membership:
        print 'slsaps: {0}'.format(i.name)
    
    g1 = gig.new_gig(the_band=slsaps, title="test gig 1", date=datetime.datetime.strptime("9/16/2013",'%m/%d/%Y').date())
    g2 = gig.new_gig(the_band=slsaps, title="test gig 2", date=datetime.datetime.strptime("9/25/2013",'%m/%d/%Y').date())
    g3 = gig.new_gig(the_band=ee, title="test gig 3", date=datetime.datetime.strptime("9/8/2013",'%m/%d/%Y').date())
    
    gigs = gig.get_gigs_for_band(slsaps)
    for g in gigs:
        print 'gig: {0}'.format(g.title)
    
    p1 = plan.new_plan(g1, member1, 1)
    p2 = plan.new_plan(g1, member2, 2)
    
    p1.set_comment("woo hoo")
    p2.set_comment("can't wait")
    
    plans=plan.get_plans_for_gig(g1)
    for p in plans:
        m=p.member.get()
        print '{0} has a plan for gig {1}: {2}'.format(m.name, g1.title, p.value)
 