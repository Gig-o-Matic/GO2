#
#  assoc class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 18 October 2013
#

from google.appengine.ext import ndb

import debug
import band
import member
import goemail
import plan
import logging
import datetime

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
    default_section_index = ndb.IntegerProperty( default=None )
    is_multisectional = ndb.BooleanProperty( default = False )
    is_occasional = ndb.BooleanProperty( default = False )
    member_name = ndb.StringProperty() # need this for ordering
    commitment_number = ndb.IntegerProperty(default=0)
    commitment_total = ndb.IntegerProperty(default=0)
    color = ndb.IntegerProperty(default=0) # see colors.py
    email_me = ndb.BooleanProperty (default=True)
    hide_from_schedule = ndb.BooleanProperty (default=False)
    created = ndb.DateTimeProperty(default=None)



    @classmethod
    def lquery(cls, *args, **kwargs):
        if debug.DEBUG:
            print('{0} query: {1}'.format(cls.__name__,args))
        return cls.query(*args, **kwargs)


def assoc_key_from_urlsafe(urlsafe):
    return ndb.Key(urlsafe=urlsafe)


def get_assoc(the_assoc_key):
    """ takes a single assoc key or a list """
    if isinstance(the_assoc_key, list):
        return ndb.get_multi(the_assoc_key)
    else:
        if not isinstance(the_assoc_key, ndb.Key):
            raise TypeError("get_assoc expects a assoc key")
        return the_assoc_key.get()

def get_assocs_from_keys(assoc_keys):
    return ndb.get_multi(assoc_keys)


def save_assocs(the_assocs):
    ndb.put_multi(the_assocs)


def get_member_keys_of_band_key(the_band_key):
    """ Return member objects by band"""        
    assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_confirmed==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    members = [a.member for a in assocs]
    return members

def get_assocs_of_band_key_for_section_key(the_band_key, the_section_key, include_occasional=True):
    args=[
            Assoc.band==the_band_key,
            Assoc.default_section==the_section_key,
            Assoc.is_confirmed==True,
            Assoc.is_invited==False
        ]
    if not include_occasional:
        args.append( Assoc.is_occasional==False )
        
    assoc_query = Assoc.lquery( *args ).order(Assoc.member_name)

#     assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_confirmed==True, Assoc.is_invited==False ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    return assocs


def get_confirmed_assocs_of_band_key(the_band_key, include_occasional=True):
    """ return all assoc keys for a band """

    args=[
            Assoc.band==the_band_key,
            Assoc.is_confirmed==True,
            Assoc.is_invited==False
        ]
    if not include_occasional:
        args.append( Assoc.is_occasional==False )
        
    assoc_query = Assoc.lquery( *args ).order(Assoc.member_name)

#     assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_confirmed==True, Assoc.is_invited==False ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    return assocs

def get_pending_members_from_band_key(the_band_key):
    """ Get all the members who are pending """
    assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_confirmed==False ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    member_keys = [a.member for a in assocs]
    members = ndb.get_multi(member_keys)
    return members

def get_invited_member_assocs_from_band_key(the_band_key):
    """ Get all the members who are pending """
    assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_invited==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    return assocs

def get_inviting_assoc_keys_from_member_key(the_member_key):
    """ Get all the band invites for a member """
    assoc_query = Assoc.lquery( Assoc.member==the_member_key, Assoc.is_invited==True )
    assocs = assoc_query.fetch(keys_only=True)
    return assocs

def get_admin_members_from_band_key(the_band_key, keys_only=False):
    """ Get all the members who are admins """
    assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_band_admin==True )
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
        assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.member==the_member_key, Assoc.is_confirmed==True )
    else:
        assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.member==the_member_key )
    assocs = assoc_query.fetch()
    if len(assocs) >= 1:
        return assocs[0]
    else:
        return None

def get_assocs_for_section_key(the_section_key, keys_only=True):
    assoc_query = Assoc.lquery(Assoc.default_section==the_section_key)
    assocs = assoc_query.fetch(keys_only=keys_only)
    return assocs

def get_member_keys_for_band_key_for_section_key(the_band_key, the_section_key):
    """ Return member objects by band with specified default section"""
    assoc_query = Assoc.lquery(Assoc.band==the_band_key,
                              Assoc.default_section==the_section_key,
                              Assoc.is_confirmed==True ).order(Assoc.member_name)
    assocs = assoc_query.fetch()
    members = [a.member for a in assocs]
    return members

def get_member_keys_of_band_key_no_section(the_band_key):
    """ Return member objects by band with no default section"""
    assoc_query = Assoc.lquery( Assoc.band==the_band_key,
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
    if the_member:
        a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
        if a:
            return a.is_band_admin
    return False


def confirm_member_for_band_key(the_member, the_band_key):
    """ assuming this member is pending, confirm them """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member.key, the_band_key=the_band_key)
    if a and not a.is_confirmed:
        a.is_confirmed = True
        # update the assoc creation date to now
        a.created=datetime.datetime.now()
        a.put()

def set_admin_for_member_key_and_band_key(the_member_key, the_band_key, the_do):
    """ find the assoc for this member and band, and make the member an admin (or take it away """
    a = get_assoc_for_band_key_and_member_key(the_member_key=the_member_key, the_band_key=the_band_key)
    if a:
        a.is_band_admin = True if (the_do==1) else False
        a.put()

def new_association(member, band, confirm=False, invited=False):
    """ associate a band and a member """
    assoc=Assoc(band=band.key, member=member.key, member_name=member.name, 
                is_confirmed=confirm, is_invited=invited, created=datetime.datetime.now())
    assoc.put()

def delete_association_from_key(the_assoc_key):
    """ delete association between member and band """
    the_assoc_key.delete()

def set_default_section(the_member_key, the_band_key, the_section_key):
    """ find the band in a member's list of assocs, and set default section """
    a = get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
    if a:
        a.default_section = the_section_key

        the_band = the_band_key.get()
        if the_section_key in the_band.sections:
            a.default_section_index = the_band.sections.index(the_section_key)
        else:
            logging.error("weird: got a default section that isn't in the band")
            a.default_section_index = None

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
        assoc_query = Assoc.lquery( Assoc.band==the_band_key, Assoc.is_confirmed==True, Assoc.is_invited==False ).order(Assoc.member_name)
    else:
        assoc_query = Assoc.lquery( Assoc.band==the_band_key ).order(Assoc.member_name)
    assocs = assoc_query.fetch(keys_only=keys_only)
    return assocs

def get_assocs_of_member_key(the_member_key, confirmed_only=False, include_hidden=True, keys_only=False):

    args=[
            Assoc.member==the_member_key,
        ]
        
    if confirmed_only:
        args.append( Assoc.is_confirmed==True )

    if not include_hidden:
        args.append( Assoc.hide_from_schedule==False)

    assoc_query = Assoc.lquery( *args )
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

def get_confirmed_assocs_of_member(the_member, include_hidden=True):
    """ Return assocs objects by member"""
    assocs = get_assocs_of_member_key(the_member.key, confirmed_only=True, include_hidden=include_hidden)
    return assocs

def confirm_invites_for_member_key(the_member_key):
    """ find invites for this member and make them real assocs """
    assoc_query = Assoc.lquery( Assoc.member==the_member_key, Assoc.is_invited==True )
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
    assoc_query = Assoc.lquery()
    assocs = assoc_query.fetch()
    return assocs

def get_all_invites():
    """ return all invited assoc keys """
    assoc_query = Assoc.lquery( Assoc.is_invited==True )
    assocs = assoc_query.fetch()
    return assocs

def confirm_user_is_member(the_user_key, the_band_key):
    """ is this member in this band? """
    a_key = get_assoc_for_band_key_and_member_key(the_user_key, the_band_key, confirmed_only = True)
    return a_key
    
def update_all_assocs():
    # add the hide_me to all assocs (as false)
    
    assoc_query = Assoc.lquery()
    assocs = assoc_query.fetch()
    for a in assocs:
        a.hide_from_schedule=False
    ndb.put_multi(assocs)
    logging.info("updated {0} assocs".format(len(assocs)))

def rest_assoc_info(the_assoc, include_id=True):
    obj = { k:getattr(the_assoc,k) for k in ('is_confirmed','is_multisectional','hide_from_schedule','is_occasional','color') }
    if the_assoc.default_section:
        obj['default_section'] = the_assoc.default_section.urlsafe()
    return obj

def reset_counts_for_band(the_band_key):
    assoc_query = Assoc.lquery(Assoc.band==the_band_key)
    assocs = assoc_query.fetch()
    for a in assocs:
        a.commitment_number = 0
        a.commitment_total = 0
    ndb.put_multi(assocs)
    logging.info("reset {0} assocs".format(len(assocs)))
