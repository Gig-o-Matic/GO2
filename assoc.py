#
# association class for Gig-o-Matic 2 - links members to bands
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from member import *
from debug import *

import plan

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
    status = ndb.IntegerProperty( default=0 ) # 0 = pending, 1 = member, 2 = band admin
    sections = ndb.KeyProperty( repeated=True )
    default_section = ndb.KeyProperty()
    section_count = ndb.ComputedProperty(lambda self: len(self.sections))
    
def new_association(band, member):
    """ associate a band and a member """
    
    # todo make sure there's not already an assoc between member and band
    the_assoc = Assoc(parent=assoc_key(), band=band.key, member=member.key, status=0)
    the_assoc.put()

def delete_association(the_band, the_member):
    """ find the association between band and member """
    assoc_query = Assoc.query(ndb.AND(Assoc.member==the_member.key, Assoc.band==the_band.key),
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()

    for an_assoc in the_assocs:
        plan.delete_plans_for_member_for_band_key(the_member, an_assoc.band)
        an_assoc.key.delete()

def get_assocs_for_member_key(the_member_key):
    """ find the association between band and member """
    assoc_query = Assoc.query(Assoc.member==the_member_key, 
                              ancestor=assoc_key())
    the_assocs = assoc_query.fetch()
    return the_assocs

def get_assocs_of_band_key(the_band_key):
    """ Return member objects by band"""
    assoc_query = Assoc.query(Assoc.band==the_band_key, ancestor=assoc_key())
    assocs = assoc_query.fetch()
    return assocs

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

    # because there might already be plans for the user with no section, take this opportunity
    # to find them and fix them
    plan.set_section_for_empty_plans_in_assoc(the_assoc, section_key)

    the_assoc.put()
    
    
def leave_section_for_assoc(assoc_key, section_key):
    the_assoc=assoc_key.get()
    if (the_assoc.sections):
        if section_key in the_assoc.sections:
            i = the_assoc.sections.index(section_key)
            the_assoc.sections.pop(i)
        if the_assoc.default_section == section_key:
            # we left our default section! Pick another one if there is one.
            if the_assoc.sections:
                the_assoc.default_section = the_assoc.sections[0]
            else:
                the_assoc.default_section = None
        the_assoc.put()
        # now, get all the plans for this member, and if they've left the section,
        # reset the section
        plan.leave_section(the_assoc, section_key, the_assoc.default_section)

def set_default_section(the_assoc_key, the_section_key):
    """ set the default section for a user's association with a band """
    the_assoc=the_assoc_key.get()
    the_assoc.default_section=the_section_key # todo make sure this is really one of our sections!
    the_assoc.put()
    # because there might already be plans for the user with no section, take this opportunity
    # to find them and fix them
    plan.set_section_for_empty_plans_in_assoc(the_assoc, the_section_key)
    
    