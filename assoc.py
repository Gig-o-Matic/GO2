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
    default_section = ndb.KeyProperty()
    section_count = ndb.ComputedProperty(lambda self: len(self.sections))
    
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

def get_assocs_for_member_key(the_member_key):
    """ find the association between band and member """
    assoc_query = Assoc.query(Assoc.member==the_member_key, 
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    return the_assocs

def get_assoc_for_band_key_and_member_key(the_band_key, the_member_key):
    """ find the association between band and member """
    assoc_query = Assoc.query(ndb.AND(Assoc.member==the_member_key, 
                                      Assoc.band==the_band_key), 
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    if len(the_assocs) == 0:
        return None #todo what to do if there's more than one plan     
    elif len(the_assocs) > 1:
        return the_assocs[0] #todo too many assocs for this band & user 
    else:
        return the_assocs[0]
        
def count_sections_for_band_key_and_member_key(the_band_key, the_member_key):
    """ see how many sections this member is in, for the given band """
    the_assoc=get_assoc_for_band_key_and_member_key(the_band_key, the_member_key)
    if (the_assoc):
        return the_assoc.section_count
    else:
        return 0

def get_member_keys_of_band_key_no_section(the_band_key):
    """ get all the members of a band who are not in a section """
    assoc_query = Assoc.query(ndb.AND(Assoc.band==the_band_key, Assoc.section_count==0),
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    member_keys=[an_assoc.member for an_assoc in the_assocs]
    return member_keys


def get_member_keys_for_section_key(the_section_key):
    assoc_query = Assoc.query(Assoc.sections==the_section_key, ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    member_keys=[an_assoc.member for an_assoc in the_assocs]
    return member_keys

def add_section_for_assoc(assoc_key, section_key):
    the_assoc=assoc_key.get()
    if (the_assoc.sections):
        if section_key not in the_assoc.sections:
            the_assoc.sections.append(section_key)
    else:
        the_assoc.sections=[section_key]
        the_assoc.default_section=section_key

    the_assoc.put()
    
    
def leave_section_for_assoc(assoc_key, section_key):
    the_assoc=assoc_key.get()
    if (the_assoc.sections):
        if section_key in the_assoc.sections:
            i = the_assoc.sections.index(section_key)
            the_assoc.sections.pop(i)

    the_assoc.put()

def set_default_section(the_assoc_key, the_section_key):
    the_assoc=the_assoc_key.get()
    the_assoc.default_section=the_section_key # todo make sure this is really one of our sections!
    the_assoc.put()
    