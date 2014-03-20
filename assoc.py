#
#  assoc class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 18 October 2013
#

from google.appengine.ext import ndb

import band
import member
import goemail
import plan

def assoc_key(member_name='assoc_key'):
    """Constructs a Datastore key for an Assoc entity with assoc_name."""
    return ndb.Key('assoc', assoc_name)

class Assoc(ndb.Model):
    """ class to hold details of the association with a band """
    band = ndb.KeyProperty()
    member = ndb.KeyProperty()
    is_confirmed = ndb.BooleanProperty( default=False )
    is_invited = ndb.BooleanProperty( default=False )
    is_band_admin = ndb.BooleanProperty( default = False )
    default_section = ndb.KeyProperty( default=None )
    is_multisectional = ndb.BooleanProperty( default = False )
    member_name = ndb.StringProperty() # need this for ordering
    
def get_member_keys_of_band_key(the_band_key):
    """ Return member objects by band"""        
    assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_confirmed==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    members = [a.member for a in assocs]
    return members

def get_confirmed_assocs_of_band_key(the_band_key):
    """ return all assoc keys for a band """
    assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_confirmed==True, Assoc.is_invited==False ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    return assocs

def get_pending_members_from_band_key(the_band_key):
    """ Get all the members who are pending """
    assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_confirmed==False ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    member_keys = [a.member for a in assocs]
    members = ndb.get_multi(member_keys)
    return members

def get_invited_member_assocs_from_band_key(the_band_key):
    """ Get all the members who are pending """
    assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_invited==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    return assocs

def get_inviting_assoc_keys_from_member_key(the_member_key):
    """ Get all the band invites for a member """
    assoc_query = Assoc.query( Assoc.member==the_member_key, Assoc.is_invited==True )
    assocs = assoc_query.fetch(keys_only=True)
    return assocs

def get_admin_members_from_band_key(the_band_key, keys_only=False):
    """ Get all the members who are admins """
    assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_band_admin==True )
    assocs = assoc_query.fetch()
    member_keys = [a.member for a in assocs]
    if keys_only:
        return member_keys
    else:
        members = ndb.get_multi(member_keys)
        return members

def get_assoc_for_band_key_and_member_key(the_member_key, the_band_key, confirmed_only=False):
    """ find the association with a band and return it """
    if confirmed_only:
        assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.member==the_member_key, Assoc.is_confirmed==True )
    else:
        assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.member==the_member_key )
    assocs = assoc_query.fetch()
    if len(assocs) >= 1:
        return assocs[0]
    else:
        return None

def get_member_keys_for_band_key_for_section_key(the_band_key, the_section_key):
    """ Return member objects by band with specified default section"""
    assoc_query = Assoc.query(Assoc.band==the_band_key,
                              Assoc.default_section==the_section_key,
                              Assoc.is_confirmed==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    members = [a.member for a in assocs]
    return members
    
def get_member_keys_of_band_key_no_section(the_band_key):    
    """ Return member objects by band with no default section"""
    assoc_query = Assoc.query( Assoc.band==the_band_key, 
                               Assoc.default_section==None,
                               Assoc.is_confirmed==True).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    members = [a.member for a in assocs]
    return members

def get_associated_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and True if there is one """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
    if a:
        return True
    else:
        return False

def get_confirmed_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and return the status """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
    if a:
        return a.is_confirmed
    else:
        return False

def get_admin_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and return the status """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
    if a:
        return a.is_band_admin
    else:
        return False
    
def confirm_member_for_band_key(the_member, the_band_key):
    """ assuming this member is pending, confirm them """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
    if a:
        a.is_confirmed = True
        a.put()

def set_admin_for_member_key_and_band_key(the_member_key, the_band_key, the_do):
    """ find the assoc for this member and band, and make the member an admin (or take it away """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member_key, the_band_key=the_band_key)
    if a:
        a.is_band_admin = True if (the_do==1) else False
        a.put()

def new_association(member, band, confirm=False, invited=False):
    """ associate a band and a member """
    assoc=Assoc(band=band.key, member=member.key, member_name=member.name, is_confirmed=confirm, is_invited=invited)
    assoc.put()
    
def delete_association_from_key(the_assoc_key):
    """ delete association between member and band """
    the_assoc_key.delete()

def set_default_section(the_member_key, the_band_key, the_section_key):
    """ find the band in a member's list of assocs, and set default section """
    a = get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
    if a:
        a.default_section = the_section_key
        a.put()

def set_multi(the_member_key, the_band_key, the_do):
    """ find the band in a member's list of assocs, and set default section """
    a = get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
    if a:
        a.is_multisectional = the_do
        a.put()

def get_assocs_of_band_key(the_band_key, confirmed_only=False, keys_only=False):
    """ go get all the assocs for a band """
    if confirmed_only:
        assoc_query = Assoc.query( Assoc.band==the_band_key, Assoc.is_confirmed==True, Assoc.is_invited==False ).order(Assoc.member_name)
    else:
        assoc_query = Assoc.query( Assoc.band==the_band_key ).order(Assoc.member_name)
    assocs = assoc_query.fetch(keys_only=keys_only)
    return assocs

def get_assocs_of_member_key(the_member_key, confirmed_only=False, keys_only=False):
    if confirmed_only:
        assoc_query = Assoc.query( Assoc.member==the_member_key, Assoc.is_confirmed==True )
    else:
        assoc_query = Assoc.query( Assoc.member==the_member_key )
    assocs = assoc_query.fetch(keys_only=keys_only)
    return assocs
    
def get_band_keys_of_member_key(the_member_key, confirmed_only=False):
    assocs = get_assocs_of_member_key(the_member_key, confirmed_only)
    band_keys = [a.band for a in assocs]
    return band_keys

def get_bands_of_member(the_member):
    """ Return band objects by member"""
    band_keys = get_band_keys_of_member_key(the_member_key = the_member.key, confirmed_only=False)
    bands = ndb.get_multi(band_keys)
    return bands

def get_confirmed_bands_of_member(the_member):
    """ Return band objects by member"""
    band_keys = get_band_keys_of_member_key(the_member_key = the_member.key, confirmed_only=True)
    bands = ndb.get_multi(band_keys)
    return bands

def get_confirmed_assocs_of_member(the_member):
    """ Return assocs objects by member"""
    assocs = get_assocs_of_member_key(the_member.key, True)
    return assocs

def confirm_invites_for_member_key(the_member_key):
    """ find invites for this member and make them real assocs """
    assoc_query = Assoc.query( Assoc.member==the_member_key, Assoc.is_invited==True )
    assocs = assoc_query.fetch()
    for a in assocs:
        a.is_invited=False
    ndb.put_multi(assocs)
    
def default_section_for_band_key(the_member, the_band_key):
    """ find the default section for a member within a given band """
    a = get_assoc_for_band_key_and_member_key(the_member.key, the_band_key)
    if a:
        return a.default_section
    else:
        return None

def change_member_name(the_member_key, member_name):
    """ find assocs for this member and change the member's name """
    the_assocs = get_assocs_of_member_key(the_member_key)
    for a in the_assocs:
        a.member_name = member_name
    ndb.put_multi(the_assocs)

def get_all_assocs():
    """ return every assoc """
    assoc_query = Assoc.query()
    assocs = assoc_query.fetch()
    return assocs

def get_all_invites():
    """ return all invited assoc keys """
    assoc_query = Assoc.query( Assoc.is_invited==True )
    assocs = assoc_query.fetch()
    return assocs
