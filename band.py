#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from debug import *

def band_key(band_name='band_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Band', band_name)

#
# class for band
#
class Band(ndb.Model):
    """ Models a gig-o-matic band """
    name = ndb.StringProperty()
    contact = ndb.UserProperty()
    website = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

def new_band(name, contact=None, website=""):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name, contact=contact, website=website)
    the_band.put()
    debug_print('new_band: added new band: {0}'.format(name))
    return the_band
        
def get_band_from_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.query(Band.name==band_name, ancestor=band_key())
    band = bands_query.fetch(1)
    debug_print('get_band_from_name: found {0} bands for name {1}'.format(len(band),band_name))
    if len(band)==1:
        return band[0]
    else:
        return None
        
def get_band_from_key(key):
    """ Return band objects by key"""
    return key.get()

def get_band_from_id(id):
    """ Return band object by id"""
    debug_print('get_band_from_id looking for id {0}'.format(id))
    return Band.get_by_id(int(id), parent=band_key()) # todo more efficient if we use the band because it's the parent?
    
def get_members_of_band(band):
    """ Return member objects by band"""
    assoc_query = Assoc.query(Assoc.band==band.key, ancestor=assoc_key())
    assocs = assoc_query.fetch()
    debug_print('get_members_of_band: got {0} assocs for band key id {1} ({2})'.format(len(assocs),band.key.id(),band.name))
    members=[a.member.get() for a in assocs]
    debug_print('get_members_of_band: found {0} members for band {1}'.format(len(members),band.name))
    return members


