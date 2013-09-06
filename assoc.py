#
# association class for Gig-o-Matic 2 - links members to bands
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from member import *
from debug import *

def assoc_key(assoc_name='assoc_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('assoc', assoc_name)

#
# class for association
#
class Assoc(ndb.Model):
    """ Models a gig-o-matic association """
    band = ndb.KeyProperty()
    member = ndb.KeyProperty()
    status = ndb.IntegerProperty( default=0 )

def new_association(band, member):
    """ associate a band and a member """
    the_assoc = Assoc(parent=assoc_key(), band=band.key, member=member.key)
    the_assoc.put()

def get_assocs_for_member(the_member):
    """ find the association between band and member """
    assoc_query = Assoc.query(Assoc.member==the_member.key, 
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    debug_print('get_assocs_for_member: got {0} assocs for {1}'.format(len(the_assocs),the_member.name))
    return the_assocs


def get_assoc_for_band_and_member(the_band, the_member):
    """ find the association between band and member """
    assoc_query = Assoc.query(ndb.And(Assoc.member==the_member.key, 
                                      Assoc.band==the_band.key), 
                              ancestor=the_gig.key)
    the_assocs = assoc_query.fetch()
    debug_print('get_assocs_for_member & band: got {0} assocs plans for {1} ({2})'.format(len(assocs),the_band.name,the_member.name))
    if len(the_assocs) == 0:
        return None #todo what to do if there's more than one plan     
    elif len(the_assocs) > 1:
        return the_assocs[0] #todo too many assocs for this band & user 
    else:
        return the_assocs[0]
