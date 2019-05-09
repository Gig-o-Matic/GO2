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
import random

def test_band():
    """make some test data"""

# delete the data if there is any
# Clear datastore entities
#      for model in [band.Band, member.Member, assoc.Assoc, gig.Gig, plan.Plan]:
#          ndb.delete_multi(model.query().fetch(999999, keys_only=True))
#   
#      # Clear memcache
#      ndb.get_context().clear_cache()      


    def make_if_not_here(name):
        the_band=band.get_band_from_condensed_name(name)
        if the_band is None:
            the_band=band.new_band(name=name)
        return the_band
    
#     member1 = member.new_member(name='Aaron', email='aoppenheimer@gmail.com', nickname='aoppenheimer', role=1)
#     member2 = member.new_member(name='Maury', nickname='mmartin')
#     member3 = member.new_member(name='Kate', email='katervw@gmail.com', nickname='katervw')
    
    slsaps=make_if_not_here("SLSAPS")
    make_if_not_here("EmperorNorton")
    ee=make_if_not_here("EE")

#     assoc.new_association(slsaps,member1)
#     assoc.new_association(ee,member1)
#     assoc.new_association(slsaps,member2)
#     assoc.new_association(slsaps,member3)

    # make a pile of random gigs for a couple of months
    n=1
    for m in range(9,12):
        for i in range(1,5):
            d=int(random.random()*30)+1
            g1 = gig.new_gig(the_band=slsaps, title="test gig {0}".format(n),
                             date=datetime.datetime.strptime("{0}/{1}/2013".format(m,d),'%m/%d/%Y').date())
            n = n + 1
    
