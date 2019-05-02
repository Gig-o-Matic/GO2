#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from requestmodel import *
from restify import rest_user_required, CSOR_Jsonify

import webapp2_extras.appengine.auth.models

import webapp2
from debug import *

import debug
import member
import goemail
import assoc
import gig
import plan
import json
import logging
import datetime
import stats
import json
import string
import rss
import gigoexceptions
from pytz.gae import pytz

def band_key(band_name='band_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Band', band_name)

#
# class for band
#
class Band(ndb.Model):
    """ Models a gig-o-matic band """
    name = ndb.StringProperty()
    lower_name = ndb.ComputedProperty(lambda self: self.name.lower())
    shortname = ndb.StringProperty()
    website = ndb.TextProperty()
    description = ndb.TextProperty()
    hometown = ndb.TextProperty()
    sections = ndb.KeyProperty( repeated=True ) # instrumental sections
    created = ndb.DateTimeProperty(auto_now_add=True)
#     time_zone_correction = ndb.IntegerProperty(default=0) # NO LONGER IN USE
    # new, real timezone stuff
    timezone = ndb.StringProperty()
    thumbnail_img = ndb.TextProperty(default=None)
    images = ndb.TextProperty(repeated=True)
    member_links = ndb.TextProperty(default=None)
    share_gigs = ndb.BooleanProperty(default=True)
    anyone_can_manage_gigs = ndb.BooleanProperty(default=True)
    anyone_can_create_gigs = ndb.BooleanProperty(default=True)
    condensed_name = ndb.ComputedProperty(lambda self: ''.join(ch for ch in self.name if ch.isalnum()).lower())
    simple_planning = ndb.BooleanProperty(default=False)
    plan_feedback = ndb.TextProperty()
    show_in_nav = ndb.BooleanProperty(default=True)
    send_updates_by_default = ndb.BooleanProperty(default=True)
    rss_feed = ndb.BooleanProperty(default=False)
    band_cal_feed_dirty = ndb.BooleanProperty(default=True)
    pub_cal_feed_dirty = ndb.BooleanProperty(default=True)
    new_member_message = ndb.TextProperty(default=None)


    @classmethod
    def lquery(cls, *args, **kwargs):
        if debug.DEBUG:
            print('{0} query'.format(cls.__name__))
        return cls.query(*args, **kwargs)

def new_band(name):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name)
    the_band.timezone = 'UTC' # every band needs this - when creating from application, done in the UI code, but should not be None
    the_band.put()
    return the_band


def band_key_from_urlsafe(the_band_keyurl):
    return ndb.Key(urlsafe=the_band_keyurl)


def forget_band_from_key(the_band_key):
    # delete all assocs
    the_assoc_keys = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=False, keys_only=True)
    ndb.delete_multi(the_assoc_keys)
    
    # delete the sections
    the_section_keys = get_section_keys_of_band_key(the_band_key)
    ndb.delete_multi(the_section_keys)

    # delete the gigs
    the_gigs = gig.get_gigs_for_band_keys(the_band_key, num=None, start_date=None)
    the_gig_keys = [a_gig.key for a_gig in the_gigs]
    
    # delete the plans
    for a_gig_key in the_gig_keys:
        plan_keys = plan.get_plans_for_gig_key(a_gig_key, keys_only = True)
        ndb.delete_multi(plan_keys)
    
    ndb.delete_multi(the_gig_keys)
    
    stats.delete_band_stats(the_band_key)
    
    # delete the band
    the_band_key.delete()

        
def get_band_from_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.lquery(Band.name==band_name, ancestor=band_key())
    band = bands_query.fetch(1)

    if len(band)==1:
        return band[0]
    else:
        return None
        
def get_band_from_condensed_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.lquery(Band.condensed_name==band_name.lower(), ancestor=band_key())
    band = bands_query.fetch(1)

    if len(band)==1:
        return band[0]
    else:
        return None

def get_band_from_key(key):
    """ Return band objects by key"""
    return key.get()

def get_band_from_id(id):
    """ Return band object by id"""

    return Band.get_by_id(int(id), parent=band_key()) # todo more efficient if we use the band because it's the parent?
    
def get_all_bands(keys_only=False):
    """ Return all objects"""
    bands_query = Band.lquery(ancestor=band_key()).order(Band.lower_name)
    all_bands = bands_query.fetch(keys_only=keys_only)
    return all_bands

def get_section_keys_of_band_key(the_band_key):
    the_band = the_band_key.get()
    if the_band:
        return the_band.sections
    else:
        return []

def get_assocs_of_band_key_by_section_key(the_band_key, include_occasional=True):
    the_band = the_band_key.get()
    the_info=[]
    the_map={}
    count=0
    for s in the_band.sections:
        the_info.append([s,[]])
        the_map[s]=count
        count=count+1
    the_info.append([None,[]]) # for 'None'
    the_map[None]=count

    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band_key, include_occasional=include_occasional)
    
    for an_assoc in the_assocs:
        the_info[the_map[an_assoc.default_section]][1].append(an_assoc)

    if the_info[the_map[None]][1] == []:
        the_info.pop(the_map[None])

    return the_info

    
def new_section_for_band(the_band, the_section_name):
    the_section = Section(parent=the_band.key, name=the_section_name)
    the_section.put()

    if the_band.sections:
        if the_section not in the_band.sections:
            the_band.sections.append(the_section.key)
    else:
        the_band.sections=[the_section.key]
    the_band.put()

    return the_section

def delete_section_key(the_section_key):
    #todo make sure the section is empty before deleting it

    # get the parent band's list of sections and delete ourselves
    the_band=the_section_key.parent().get()
    if the_section_key in the_band.sections:
        i=the_band.sections.index(the_section_key)
        the_band.sections.pop(i)
        the_band.put()
    the_section_key.delete()
    
    # todo The app doesn't let you delete a section unless it's empty. But for any gig,
    # it's possible that the user has previously specified that he wants to play in the
    # section to be deleted. So, find plans with the section set, and reset the section
    # for that plan back to None to use the default.
    plan.remove_section_from_plans(the_section_key)

def get_feedback_strings(the_band):
    return the_band.plan_feedback.split('\n')

def make_band_cal_dirty(the_band):
    the_band.band_cal_feed_dirty = True
    the_band.pub_cal_feed_dirty = True
    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band.key, include_occasional=True)
    the_member_keys = [a.member for a in the_assocs]
    the_members = ndb.get_multi(the_member_keys)
    for m in the_members:
        m.cal_feed_dirty = True
    ndb.put_multi(the_members+[the_band])

#
# class for section
#
class Section(ndb.Model):
    """ Models an instrument section in a band """
    name = ndb.StringProperty()


def new_section(parent, name):
    return Section(parent=parent, name=name)


def section_key_from_urlsafe(the_section_keyurl):
    return ndb.Key(urlsafe=the_section_keyurl)


def set_section_indices(the_band):
    """ for every assoc in the band, set the default_section_index according to the section list in the band """

    map = {}
    for i,s in enumerate(the_band.sections):
        map[s] = i
    map[None] = None

    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band.key, include_occasional=True)
    for a in the_assocs:
        a.default_section_index = map[a.default_section]

    ndb.put_multi(the_assocs)

