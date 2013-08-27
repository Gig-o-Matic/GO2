#
# gig class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from debug import *

#
# class for gig
#
class Gig(ndb.Model):
    """ Models a gig-o-matic gig """
    title = ndb.TextProperty()
    contact = ndb.UserProperty()
    details = ndb.TextProperty()
    date = ndb.DateProperty()
    call = ndb.TimeProperty()

def new_gig(band, title, contact=None, details="", date=None, call=None):
    """ Make and return a new gig """
    the_gig = Gig(parent=band.key, title=title, contact=contact, details=details, date=date, call=call)
    the_gig.put()
    debug_print('new_gig: added new gig: {0} on {1}'.format(title,str(date)))
    return the_gig
                
def get_gig_from_key(key):
    """ Return gig objects by key"""
    return key.get()
    
def get_gig_from_id(band, id):
    """ Return gig object by id; needs the key for the parent, which is the band for this gig"""
    debug_print('get_gig_from_id looking for id {0}'.format(id))
    return Gig.get_by_id(int(id), parent=band.key) # todo more efficient if we use the band because it's the parent?
    
def get_gigs_for_band(band,num=None):
    """ Return gig objects by band"""
    gig_query = Gig.query(ancestor=band.key).order(Gig.date)
    gigs = gig_query.fetch(limit=num)
    debug_print('get_gigs_for_band: got {0} gigs for band key id {1} ({2})'.format(len(gigs),band.key.id(),band.name))
    return gigs
    
def get_gigs_for_band_for_dates(band,start_date, end_date):
    """ Return gig objects by band"""
    gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                  Gig.date <= end_date), \
                                  ancestor=band.key).order(Gig.date)
    gigs = gig_query.fetch()
    debug_print('get_gigs_for_band_for_dates: got {0} gigs for band key id {1} ({2})'.format(len(gigs),band.key.id(),band.name))
    return gigs

