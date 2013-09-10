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
    sections = ndb.KeyProperty( repeated=True )

def new_association(band, member):
    """ associate a band and a member """
    
    # todo make sure there's not already an assoc between member and band
    the_assoc = Assoc(parent=assoc_key(), band=band.key, member=member.key)
    the_assoc.put()

def delete_association(the_band, the_member):
    """ find the association between band and member """
    assoc_query = Assoc.query(ndb.AND(Assoc.member==the_member.key, Assoc.band==the_band.key),
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch(keys_only=True)
    debug_print('delete_association: got {0} assocs for {1} {2}'.format(len(the_assocs),
                                                                        the_band.name,
                                                                        the_member.name))
    
    if len(the_assocs)>0:
        ndb.delete_multi(the_assocs)

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

def add_section_for_assoc(assoc_key, section_key):
    
    print 'adding the section to the assoc'
    
    the_assoc=assoc_key.get()
    if (the_assoc.sections):
        if section_key not in the_assoc.sections:
            the_assoc.sections.append(section_key)
    else:
        the_assoc.sections=[section_key]

    the_assoc.put()