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


    def make_if_not_here(name):
        the_band=band.get_band_from_name(name)
        if the_band is None:
            the_band=band.new_band(name=name, website="www.{0}.org".format(name))
        return the_band

    slsaps=make_if_not_here("SLSAPS")
    make_if_not_here("EmperorNorton")
    make_if_not_here("EE")
    
    member1 = member.new_member(first_name='Aaron', last_name='Oppenheimer', email='aoppenheimer@gmail.com', nickname='aoppenheimer')
    member2 = member.new_member(first_name='Maury', last_name='Martin', nickname='mmartin')
    member3 = member.new_member(first_name='Kevin', last_name='Leppman', nickname='kleppman')
    
    assoc.new_association(slsaps,member1)
    assoc.new_association(slsaps,member2)
    assoc.new_association(slsaps,member3)

    membership = band.get_members_of_band(slsaps)
    for i in membership:
        print 'slsaps: {0}'.format(i.first_name)
    
    g1 = gig.new_gig(the_band=slsaps, title="test gig 1", date=datetime.datetime.strptime("8/16/2013",'%m/%d/%Y').date())
    g2 = gig.new_gig(the_band=slsaps, title="test gig 2", date=datetime.datetime.strptime("8/25/2013",'%m/%d/%Y').date())
    
    gigs = gig.get_gigs_for_band(slsaps)
    for g in gigs:
        print 'gig: {0}'.format(g.title)
    
    plan.new_plan(g1, member1, 1)
    plan.new_plan(g1, member2, 2)
    
    plans=plan.get_plans_for_gig(g1)
    for p in plans:
        m=p.member.get()
        print '{0} has a plan for gig {1}: {2}'.format(m.first_name, g1.title, p.value)
 