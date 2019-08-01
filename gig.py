"""

 gig class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb

import webapp2

import gigarchive
import gigcomment
import assoc
import comment
import plan
import cryptoutil
import stats
import band

# from pytz.gae import pytz
import pytz

import datetime
from dateutil import parser

#
# class for gig
#
class Gig(ndb.Model):
    """ Models a gig-o-matic gig """
    title = ndb.StringProperty()
    contact = ndb.KeyProperty()
    details = ndb.TextProperty()
    setlist = ndb.TextProperty()
    created_date = ndb.DateProperty( auto_now_add=True )
    date = ndb.DateTimeProperty( default=True)
    enddate = ndb.DateTimeProperty( default=None )
    trueenddate = ndb.ComputedProperty(lambda self: self.enddate if self.enddate else self.date)
    calltime = ndb.TextProperty( default=None )
    settime = ndb.TextProperty( default=None )
    endtime = ndb.TextProperty( default=None )
    sorttime = ndb.IntegerProperty( default=None )
    address = ndb.TextProperty( default=None )
    dress = ndb.TextProperty( default=None )
    paid = ndb.TextProperty( default=None )
    leader = ndb.TextProperty( default=None )
    postgig = ndb.TextProperty( default=None )
    status = ndb.IntegerProperty( default=0 ) # 1=confirmed, 2=cancelled, 3=asking
    archive_id = ndb.TextProperty( default=None )
    is_private = ndb.BooleanProperty(default=False )    
    is_archived = ndb.ComputedProperty(lambda self: self.archive_id is not None)
    is_canceled = ndb.ComputedProperty(lambda self: self.status == 2)
    is_confirmed = ndb.ComputedProperty(lambda self: self.status == 1)
    comment_id = ndb.TextProperty( default = None)
    creator = ndb.KeyProperty()
    invite_occasionals = ndb.BooleanProperty(default=True)
    was_reminded = ndb.BooleanProperty(default=False)
    hide_from_calendar = ndb.BooleanProperty(default=False)
    rss_description = ndb.TextProperty( default=None )
    trashed_date = ndb.DateTimeProperty( default=None )
    is_in_trash = ndb.ComputedProperty(lambda self: self.trashed_date is not None )
    default_to_attending = ndb.BooleanProperty( default=False )

    status_names=["Unconfirmed","Confirmed!","Cancelled!"]
    
    def gigtime(self):
        if self.calltime:
            return self.calltime
        elif self.settime:
            return self.settime
        else:
            return None

    # gig call, start, and end times are strings that may or may not be times
    def _make_sort_time(self):

        def _time_as_minutes(n):
            try:
                t = parser.parse(n).time()
                return t.hour * 60 + t.minute
            except ValueError:
                return 0 # just sort the non-parsable values first

        # do some work to figure out the actual time of the gig
        timestring = self.calltime if self.calltime else self.settime

        if timestring:
            self.sorttime = _time_as_minutes(timestring)
        else:
            self.sorttime = 0
        self.put()

    def set_calltime(self, time):
        self.calltime = time
        self.sorttime = None

    def set_settime(self, time):
        self.settime = time
        self.sorttime = None

    def set_endtime(self, time):
        self.endtime = time

    # overload the put method to make sure we set the sorting time properly
    def put(self):
        if self.sorttime is None:
            self._make_sort_time()
        super(Gig, self).put()

#
# Functions to make and find gigs
#

def new_gig(the_band, title, creator, date=None, contact=None, details="", setlist="", call=None):
    """ Make and return a new gig """
    if date is None:
        date = datetime.datetime.now()
    the_gig = Gig(parent=the_band.key, title=title, contact=contact, \
                    details=details, setlist=setlist, date=date, calltime=call, \
                    creator=creator)
    the_gig.put()
    stats.update_band_gigs_created_stats(the_band.key)
    
    return the_gig


def gig_key_from_urlsafe(urlsafe):
    return ndb.Key(urlsafe=urlsafe)


def get_gig_from_key(key):
    """ Return gig objects by key"""
    return key.get()
        
def adjust_date_for_band(the_band, the_date):

# DON'T THINK WE NEED THIS ANYMORE

#     if the_band.time_zone_correction:
#         # this band is in a non-UTC time zone!
#         the_date=the_date+datetime.timedelta(hours=the_band.time_zone_correction)
#     the_date = the_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return the_date
    
def get_gigs_for_band_keys(the_band_key_list, num=None, start_date=None, end_date=None, show_canceled=True, show_only_public=False, confirmed_only=False, show_past=False, keys_only=False):
    """ Return gig objects by band """
        
    if (type(the_band_key_list) is not list):
        the_band_key_list = [the_band_key_list]

    if show_past is False:
        params = [ Gig.is_archived == False ]
    else:
        params = []

    orderby = Gig.trueenddate

    if start_date:
        start_date = adjust_date_for_band(the_band_key_list[0].get(), start_date)
        params.append( Gig.trueenddate >= start_date )

    if end_date:
        end_Date = adjust_date_for_band(the_band_key_list[0].get(), end_date)
        params.append( Gig.trueenddate <= end_date )
        
    if not show_canceled:
        params.append( Gig.is_canceled == False )
    
    if show_only_public:
        params.append( Gig.is_private == False )

    if confirmed_only:
        params.append( Gig.status == 1 )

    # params.append( Gig.is_in_trash == False )

    all_gigs = []
    for a_band_key in the_band_key_list:
        gig_query = Gig.query(*params, ancestor=a_band_key).order(orderby)
        the_gigs = gig_query.fetch()
        the_gigs = [x for x in the_gigs if not (hasattr(x,"trashed_date") and x.is_in_trash)]
        all_gigs.append(the_gigs)

    # now we have several lists of gigs - merge them
    if len(all_gigs) == 0:
        return None
    elif len(all_gigs) == 1:
        if num is None:
            return all_gigs[0]
        else:
            return all_gigs[:num]
    else:
        # merge the gigs
        sorted_gigs = []
        list1 = all_gigs.pop()    
        while all_gigs:
            list2 = all_gigs.pop()    
            while (list1 and list2):
                if (list1[0].date <= list2[0].date): # Compare both heads
                    item = list1.pop(0) # Pop from the head
                    sorted_gigs.append(item)
                else:
                    item = list2.pop(0)
                    sorted_gigs.append(item)

            # Add the remaining of the lists
            sorted_gigs.extend(list1 if list1 else list2)
            # now prepare to loop back
            list1 = sorted_gigs
            sorted_gigs = []

    sorted_gigs = list1

    if num is None:
        return list1
    else:
        return list1[:num]
    
    
    
def get_gigs_for_band_key_for_dates(the_band_key, start_date, end_date, get_canceled=True, get_archived=False):
    """ Return gig objects by band, past gigs OK """

    if start_date:
        start_date = adjust_date_for_band(the_band_key.get(), start_date)

    if end_date:
        end_date = adjust_date_for_band(the_band_key.get(), end_date)

    args = [
        Gig.date >= start_date,
        Gig.date < end_date,
        Gig.is_in_trash == False
    ]

    if get_canceled == False:
        args.append(Gig.is_canceled == False)

    if get_archived == False:
        args.append(Gig.is_archived == False)

    gig_query = Gig.query(*args, ancestor=the_band_key).order(Gig.date)
    gigs = gig_query.fetch()
    
    return gigs


def get_all_gig_dates_for_band(the_band_key, get_canceled=True, get_archived=True):
    args = [
        Gig.is_in_trash == False
    ]

    if get_canceled == False:
        args.append(Gig.is_canceled == False)

    if get_archived == False:
        args.append(Gig.is_archived == False)

    gig_query = Gig.query(*args, ancestor=the_band_key)
    gig_dates = gig_query.fetch(projection=[Gig.date])
    # gig_dates = gig_query.fetch()
    return gig_dates


def get_gigs_for_creation_date(the_band_key, the_creation_date):
    """ return gigs created on a particular date """
    gig_query = Gig.query(Gig.created_date == the_creation_date, ancestor=the_band_key)
    gigs = gig_query.fetch()
    return gigs
    

def get_gigs_for_member_for_dates(the_member, start_date, end_date, get_canceled=True):
    """ return gig objects for the bands of a member """
    the_bands = assoc.get_confirmed_bands_of_member(the_member)

    all_gigs = []
    if len(the_bands) > 0:
        if start_date:
            start_date = adjust_date_for_band(the_bands[0], start_date)

        if end_date:
            end_date = adjust_date_for_band(the_bands[0], end_date)

        for a_band in the_bands:
            all_gigs.extend(get_gigs_for_band_key_for_dates(the_band_key=a_band.key, \
                                                        start_date=start_date, \
                                                        end_date=end_date,
                                                        get_canceled=get_canceled))
    return all_gigs

def get_gigs_for_contact_key(the_contact_key, the_band_key):
    """ pass in a member key, get back the gigs for which this member is the contact """
    gig_query = Gig.query(Gig.contact == the_contact_key, ancestor=the_band_key)
    gigs = gig_query.fetch()
    return gigs

def reset_gigs_for_contact_key(the_member_key, the_band_key):
    """ find gigs for which member is contact, and set contact to None """
    gigs = get_gigs_for_contact_key(the_contact_key=the_member_key, the_band_key=the_band_key)
    for g in gigs:
        g.contact = None
    ndb.put_multi(gigs)

def get_old_gig_keys(end_date):
    """ Return gig objects by band, past gigs OK """
    
    # todo do we need to adjust the date?
    
    gig_query = Gig.query(ndb.AND(Gig.is_archived == False, \
                                  Gig.trueenddate <= end_date))
    gigs = gig_query.fetch(10, keys_only=True)
    return gigs

def get_trashed_gigs_for_band_key(the_band_key):
    """ get non-archived gigs that are currently in the trash """

    params = [ Gig.is_archived == False ]
    params.append( Gig.is_in_trash == True )
    gig_query = Gig.query(*params, ancestor=the_band_key)
    the_gigs = gig_query.fetch()
    # sorted(the_gigs, key=lambda x:x.date)
    return the_gigs

def get_old_trashed_gigs(minimum_age=None):
    """ get non-archived gigs that are currently in the trash """

    params = [ Gig.is_archived == False ]
    params.append( Gig.is_in_trash == True )
    if minimum_age:
        max_date = datetime.datetime.now() - datetime.timedelta(days=minimum_age)
        params.append( Gig.trashed_date <= max_date )

    gig_query = Gig.query(*params)
    the_gigs = gig_query.fetch()
    # sorted(the_gigs, key=lambda x:x.date)
    return the_gigs

def get_sorted_gigs_from_band_keys(the_band_keys=[], include_canceled=False):
    all_gigs=[]
    for bk in the_band_keys:
        b = bk.get()                       
        today_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone(b.timezone)), datetime.time(0,0,0))
        some_gigs = get_gigs_for_band_keys(bk, show_canceled=include_canceled, start_date=today_date)
        all_gigs = all_gigs + some_gigs

    all_gigs = sorted(all_gigs, key=lambda gig: (gig.date, gig.sorttime))
    return all_gigs
    
def set_sections_for_empty_plans(the_gig):
    """ For this gig, get all plans. For plans with no section set, get the users default and set it """
    """ This is used when freezing a gig's plans """
    
    the_plan_keys = plan.get_plans_for_gig_key(the_gig.key, keys_only=True)
    the_band_key = the_gig.key.parent()
    for a_plan_key in the_plan_keys:
        a_plan = a_plan_key.get()
        if a_plan.section is None:
            the_member_key = a_plan.member
            the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
            if the_assoc:
                a_plan.section = the_assoc.default_section
                a_plan.put()
            
def make_archive_for_gig_key(the_gig_key):
    """ makes an archive for a gig - files away all the plans, then delete them """
    
    archive_id = gigarchive.make_archive_for_gig_key(the_gig_key)
    if archive_id:
        the_gig = the_gig_key.get()
        if the_gig.archive_id:
            gigarchive.delete_archive(the_gig.archive_id)
        the_gig.archive_id = archive_id
        the_gig.put()

        # keep the old plans around so the gig still shows up on calendar feeds. The plans
        # are no longer editable through the UI, they just linger forever on calendar feeds
        # if you look back in time.
        #        # also delete any plans, since they're all now in the archive
        #        plan.delete_plans_for_gig_key(the_gig_key)


#    the_yes_url, the_no_url = gig.get_confirm_urls(the_member, the_gig)
def get_confirm_urls(the_member, the_gig):
    """return three urls which encode the member and the gig, and a yes or no"""
    
    yes_string = "{0}+{1}+1".format(the_member.key.urlsafe(), the_gig.key.urlsafe())
    yes_code = cryptoutil.encrypt_string(yes_string)
    yes_url =  webapp2.uri_for('gig_answerlink', _full=True, c=yes_code)

    no_string = "{0}+{1}+0".format(the_member.key.urlsafe(), the_gig.key.urlsafe())
    no_code = cryptoutil.encrypt_string(no_string)
    no_url =  webapp2.uri_for('gig_answerlink', _full=True, c=no_code)

    snooze_string = "{0}+{1}+2".format(the_member.key.urlsafe(), the_gig.key.urlsafe())
    snooze_code = cryptoutil.encrypt_string(snooze_string)
    snooze_url =  webapp2.uri_for('gig_answerlink', _full=True, c=snooze_code)

    return yes_url, no_url, snooze_url

#   confirm user is either superuser, a band admin, or the contact for a gig.
def can_edit_gig(the_user, the_gig=None, the_band=None):

    authorized = False
    if the_user.is_superuser:
        authorized = True
    elif the_gig and the_gig.contact == the_user.key:
        authorized = True
    elif the_gig is None and the_band and the_band.anyone_can_create_gigs:
        authorized = True
    elif the_gig is not None and the_band and the_band.anyone_can_manage_gigs:
        authorized = True
    elif the_band and assoc.get_admin_status_for_member_for_band_key(the_user, the_band.key):
        authorized = True

    return authorized

def delete_gig_completely(the_gig):
    """ fully delete a gig, its archive, comments, plans, and itself """
    if the_gig:
        if the_gig.is_archived:
            gigarchive.delete_archive(the_gig.archive_id)
        if the_gig.comment_id:
            gigcomment.delete_comment(the_gig.comment_id)
        comment.delete_comments_for_gig_key(the_gig.key)
        plan.delete_plans_for_gig_key(the_gig.key)
        the_gig.key.delete()


def rest_gig_info(the_gig, include_id=True):
    obj = { k:getattr(the_gig,k) for k in ('title','details','setlist','date','calltime','settime',
                                            'endtime','address','paid','dress','leader','postgig','status','is_in_trash') }
    obj['contact'] = the_gig.contact.urlsafe() if the_gig.contact else ""
    obj['band'] = the_gig.key.parent().urlsafe()
    if include_id:
        obj['id'] = the_gig.key.urlsafe()
    return obj


def rest_gig_plan_info(the_plans):
    member_keys = [i['the_member_key'] for i in the_plans]
    members = ndb.get_multi(member_keys)
    member_names = dict(zip(member_keys,[m.display_name for m in members]))

    plans = []
    for info_block in the_plans:
        info = {}
        info['the_plan'] = plan.rest_plan_info(info_block['the_plan'])
        info['the_member_key'] = info_block['the_member_key'].urlsafe()
        info['the_member_name'] = member_names[info_block['the_member_key']]
        if info['the_plan']['section'] == '':
            if info_block['the_assoc'].default_section:
                info['the_plan']['section'] = info_block['the_assoc'].default_section.urlsafe()
        plans.append(info)
    return plans


def rewrite_all_gigs():
    band_keys = band.get_all_bands(keys_only=True)
    for k in band_keys:
        gig_query = Gig.query(ancestor=k)
        g = gig_query.fetch()
        print("\n\n{} gigs\n\n".format(len(g)))
        ndb.put_multi(g)
