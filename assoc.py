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

def new_association(band, member):
    """ associate a band and a member """
    the_assoc = Assoc(parent=assoc_key(), band=band.key, member=member.key)
    the_assoc.put()

def get_members_of_band(band):
    """ Return member objects by band"""
    assoc_query = Assoc.query(Assoc.band==band.key, ancestor=assoc_key())
    assocs = assoc_query.fetch()
    debug_print('get_members_of_band: got {0} assocs for band key id {1} ({2})'.format(len(assocs),band.key.id(),band.name))
    members=[a.member.get() for a in assocs]
    debug_print('get_members_of_band: found {0} members for band {1}'.format(len(members),band.name))
    return members

