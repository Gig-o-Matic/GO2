#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb

import debug
import assoc
import gig
import plan
import stats
import logging


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
    sections = ndb.KeyProperty(repeated=True)  # instrumental sections
    created = ndb.DateTimeProperty(auto_now_add=True)
    timezone = ndb.StringProperty(default='UTC')
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


def get_band(the_band_key):
    """ takes a single band key or a list """
    if isinstance(the_band_key, list):
        return ndb.get_multi(the_band_key)
    else:
        if not isinstance(the_band_key, ndb.Key):
            raise TypeError("get_band expects a band key")
        return the_band_key.get()


def put_band(the_band):
    """ takes a single band object or a list """
    if isinstance(the_band, list):
        return ndb.put_multi(the_band)
    else:
        if not isinstance(the_band, Band):
            raise TypeError("put_band expects a band")
        return the_band.put()


def new_band(name):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name)
    put_band(the_band)
    return the_band


def band_from_urlsafe(the_band_keyurl, key_only=False):
    try:
        k = ndb.Key(urlsafe=the_band_keyurl)
    except Exception as e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            logging.error("invalid urlsafe passed to band_from_urlsafe")
            return None
        else:
            raise
    if key_only:
        return k
    else:
        return get_band(k)


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


def get_band_from_condensed_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.lquery(Band.condensed_name==band_name.lower(), ancestor=band_key())
    band = bands_query.fetch(1)

    if len(band)==1:
        return band[0]
    else:
        return None


def get_all_bands(keys_only=False):
    """ Return all objects"""
    bands_query = Band.lquery(ancestor=band_key()).order(Band.lower_name)
    all_bands = bands_query.fetch(keys_only=keys_only)
    return all_bands


def get_assocs_of_band_key_by_section_key(the_band_key, include_occasional=True):
    the_band = get_band(the_band_key)
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
    s = Section(parent=parent, name=name)
    put_section(s)
    return s


def section_from_urlsafe(the_section_keyurl, key_only=False):
    try:
        k = ndb.Key(urlsafe=the_section_keyurl)
    except Exception as e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            logging.error("invalid urlsafe passed to section_from_urlsafe")
            return None
        else:
            raise
    if key_only:
        return k
    else:
        return get_section(k)


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


def new_section_for_band(the_band, the_section_name):
    the_section = Section(parent=the_band.key, name=the_section_name)
    put_section(the_section)

    if the_band.sections:
        if the_section not in the_band.sections:
            the_band.sections.append(the_section.key)
    else:
        the_band.sections=[the_section.key]
    put_band(the_band)

    return the_section


def delete_section_key(the_section_key):
    # todo make sure the section is empty before deleting it

    # get the parent band's list of sections and delete ourselves
    the_band = get_band(the_section_key.parent())
    if the_section_key in the_band.sections:
        i = the_band.sections.index(the_section_key)
        the_band.sections.pop(i)
        put_band(the_band)

    # if any member is using this section, reset them to no section
    assoc_keys = assoc.get_assocs_for_section_key(the_section_key, keys_only=True)
    if assoc_keys:
        assocs = assoc.get_assoc(assoc_keys)
        for a in assocs:
            a.default_section = None
        assoc.put_assoc(assocs)

    # For any gig, it's possible that the user has previously specified that he wants to play in the
    # section to be deleted. So, find plans with the section set, and reset the section
    # for that plan back to None to use the default.
    plan.remove_section_from_plans(the_section_key)

    the_section_key.delete()


def get_section_keys_of_band_key(the_band_key):
    the_band = get_band(the_band_key)
    if the_band:
        return the_band.sections
    else:
        return []


def get_section(the_section_key):
    """ takes a single section key or a list """
    if isinstance(the_section_key, list):
        return ndb.get_multi(the_section_key)
    else:
        if not isinstance(the_section_key, ndb.Key):
            raise TypeError("get_section expects a section key")
        return the_section_key.get()


def put_section(the_section):
    """ takes a single section key or a list """
    if isinstance(the_section, list):
        return ndb.put_multi(the_section)
    else:
        if not isinstance(the_section, Section):
            raise TypeError("put_section expects a section")
        return the_section.put()


def rest_band_info(the_band, the_assoc=None, include_id=True, name_only=False):

    obj = { k:getattr(the_band,k) for k in ('name','shortname') }

    if name_only==False:
        for k in ('description','simple_planning'):
            obj[k] = getattr(the_band,k)

        # obj = { k:getattr(the_band,k) for k in ('name','shortname','description','simple_planning') }
        obj['plan_feedback'] = map(str.strip,str(the_band.plan_feedback).split("\n")) if the_band.plan_feedback else ""
        the_sections = get_section(the_band.sections)
        obj['sections'] = [{'name':s.name, 'id':s.key.urlsafe()} for s in the_sections]

        if include_id:
            obj['id'] = the_band.key.urlsafe()

        if the_assoc:
            obj.update( assoc.rest_assoc_info(the_assoc) )

    return obj

