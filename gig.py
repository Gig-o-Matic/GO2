"""

 gig class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb
from requestmodel import *
from restify import rest_user_required, CSOR_Jsonify

import webapp2_extras.appengine.auth.models

import webapp2

import member
import band
import plan
import goemail
import gigarchive
import gigcomment
import assoc
import comment
import plan
import cryptoutil
import rss
# import jinja2env
import jinja2ext
import logging
import gigoexceptions

from pytz.gae import pytz
from webapp2_extras.i18n import gettext as _

from clone import clone_entity

import datetime
from dateutil import parser
import babel

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
    return the_gig
                
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

    if start_date:
        start_date = adjust_date_for_band(the_band_key_list[0].get(), start_date)
        params.append( Gig.date >= start_date )
        
    if end_date:
        end_Date = adjust_date_for_band(the_band_key_list[0].get(), end_date)
        params.append( Gig.date <= end_date )
    
    if not show_canceled:
        params.append( Gig.is_canceled == False )
    
    if show_only_public:
        params.append( Gig.is_private == False )

    if confirmed_only:
        params.append( Gig.status == 1 )

    # params.append( Gig.is_in_trash == False )

    all_gigs = []
    for a_band_key in the_band_key_list:
        gig_query = Gig.query(*params, ancestor=a_band_key).order(Gig.date)
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
    
    
    
def get_gigs_for_band_key_for_dates(the_band_key, start_date, end_date, get_canceled=True):
    """ Return gig objects by band, past gigs OK """

    if start_date:
        start_date = adjust_date_for_band(the_band_key.get(), start_date)

    if end_date:
        end_date = adjust_date_for_band(the_band_key.get(), end_date)

    if get_canceled:
        gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                      Gig.date <= end_date), \
                                      Gig.is_in_trash == False, \
                                      Gig.is_archived == False, \
                                      ancestor=the_band_key).order(Gig.date)
    else:
        gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                      Gig.date <= end_date,
                                      Gig.is_in_trash == False, \
                                      Gig.is_archived == False, \
                                      Gig.is_canceled == False), \
                                      ancestor=the_band_key).order(Gig.date)
    gigs = gig_query.fetch()
    
    return gigs

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
                                  Gig.date <= end_date))
    gigs = gig_query.fetch(keys_only=True)
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

#
#
# routines for turning gig into info for REST api
#
#
def _RestGigInfo(the_gig):
    obj = { k:getattr(the_gig,k) for k in ('title','date','status') }
    obj['id'] = the_gig.key.urlsafe()
    obj['time'] = the_gig.calltime if the_gig.calltime else the_gig.settime
    obj['band'] =  the_gig.key.parent().urlsafe()
    return obj

#
#
# Handlers
#
#

def _makeInfoPageInfo(the_user, the_gig, the_band_key):
    gig_key = the_gig.key

    the_assocs = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=True, keys_only=False)

    
    # get all the plans for this gig - might actually not be any yet.
    all_plans = plan.get_plans_for_gig_key(gig_key, keys_only=False)
    
    # now, for each associated member, find or make a plan
    the_plans = []
    the_new_plans = [] # in case we need to make new ones

    the_plan_counts={}
    for i in range(len(plan.plan_text)):
        the_plan_counts[i]=0
                                
    need_empty_section = False
    for the_assoc in the_assocs:
        a_member_key = the_assoc.member
        new_plan = False
        
        for p in all_plans:
            if p.member == a_member_key:
                the_plan = p
                break
        else:
            # no plan? make a new one
            planval = 0
            if ( the_gig.default_to_attending ):
                planval = 1

            the_plan = plan.Plan(parent=gig_key, member=a_member_key, value=planval, comment="", section=None)
            the_new_plans.append(the_plan)
            new_plan = True

        if (not the_assoc.is_occasional) or \
           (the_assoc.is_occasional and the_plan.value != 0) or \
           (a_member_key == the_user.key) or \
           the_user.is_superuser:
            if the_plan.section==None and the_assoc.default_section==None:
                need_empty_section = True
            info_block={}
            info_block['the_gig_key'] = the_gig.key
            info_block['the_plan'] = the_plan
            info_block['the_member_key'] = a_member_key
            info_block['the_band_key'] = the_band_key
            info_block['the_assoc'] = the_assoc
            if the_plan.section is not None:
                info_block['the_section'] = the_plan.section
            else:
                info_block['the_section'] = the_assoc.default_section            
            the_plans.append(info_block)
            the_plan_counts[the_plan.value] += 1

    if the_new_plans:
        ndb.put_multi(the_new_plans)

    the_section_keys = band.get_section_keys_of_band_key(the_band_key)
    the_sections = ndb.get_multi(the_section_keys)
    if need_empty_section:
        the_sections.append(None)
        
    if len(the_section_keys)==0:
        band_has_sections = False
    else:
        band_has_sections = True

    return the_plans, the_plan_counts, the_sections, band_has_sections


class InfoPage(BaseHandler):
    """ class to serve the gig info page """

    @user_required
    def get(self):    
        self._make_page(self.user)

    def _make_page(self, the_user):

        # find the gig we're interested in
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            self.response.write('no gig key passed in!')
            return # todo figure out what to do if there's no ID passed in

        gig_key = ndb.Key(urlsafe=gig_key_str)
        the_gig = gig_key.get()

        if the_gig is None:
            template_args = {}
            self.render_template('no_gig_found.html', template_args)
            return # todo figure out what to do if we didn't find it

        the_comment_text = None
        if the_gig.comment_id:
            the_comment_text = gigcomment.get_comment(the_gig.comment_id)

        if not the_gig.is_archived:

            the_band_key = the_gig.key.parent()
            the_plans, the_plan_counts, the_sections, band_has_sections = _makeInfoPageInfo(the_user, the_gig, the_band_key)

            # is the current user a band admin?
            the_user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key)
            the_band = the_band_key.get()
            user_can_edit = can_edit_gig(the_user, the_gig, the_band)
            user_can_create = can_edit_gig(the_user, None, the_band)

            datestr = member.format_date_for_member(the_user, the_gig.date, format="long")
            if the_gig.enddate:
                enddatestr = u' - {0}'.format(member.format_date_for_member(the_user, the_gig.enddate, format="long"))
            else:
                enddatestr = ''

            template_args = {
                'gig' : the_gig,
                'date_str' : datestr,
                'enddate_str' : enddatestr,
                'the_plans' : the_plans,
                'the_sections' : the_sections,
                'comment_text' : the_comment_text,
                'band_has_sections' : band_has_sections,
                'the_user_is_band_admin' : the_user_is_band_admin,
                'user_can_edit' : user_can_edit,
                'user_can_create' : user_can_create,
                'the_plan_counts' : the_plan_counts
            }
            self.render_template('gig_info.html', template_args)

        else:
            # this is an archived gig
            the_archived_plans = gigarchive.get_archived_plans(the_gig.archive_id)
            template_args = {
                'gig' : the_gig,
                'archived_plans' : the_archived_plans,
                'comment_text' : the_comment_text
            }
            self.render_template('gig_archived_info.html', template_args)
            


class EditPage(BaseHandler):
    """ A class for rendering the gig edit page """

    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        if self.request.get("new", None) is not None:
            the_gig = None
            is_new = True
            
            the_band_keyurl = self.request.get("bk", None)
            if the_band_keyurl is None:
                return # figure out what to do
            else:
                the_band = ndb.Key(urlsafe = the_band_keyurl).get()
        else:
            the_gig_key = self.request.get("gk", None)
            if (the_gig_key is None):
                return # figure out what to do
                
            the_gig = ndb.Key(urlsafe=the_gig_key).get()
            if the_gig is None:
                self.response.write('did not find a band or gig!')
                return # todo figure out what to do if we didn't find it
            is_new = False
            the_band = the_gig.key.parent().get()

        # are we authorized to edit this gig?
        if can_edit_gig(self.user, the_gig, the_band) is False:
            # logging.error(u'user {0} trying to edit a gig for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))
            raise gigoexceptions.GigoException('user {0} trying to edit a gig for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))

        the_dupe = self.request.get("dupe", 0)

#   don't think we need this...
#         if is_new:
#             user_is_band_admin = False
#         else:
#             user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(the_user, the_gig.key.parent())
            
        template_args = {
            'gig' : the_gig,
            'the_band' : the_band,
#             'user_is_band_admin': user_is_band_admin,
            'is_dupe' : the_dupe,
            'newgig_is_active' : is_new,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('gig_edit.html', template_args)
        
    @user_required        
    def post(self):
        """post handler - if we are edited by the template, handle it here 
           and redirect back to info page"""


        the_gig_key = self.request.get("gk", '0')
        
        if (the_gig_key == '0'):
            the_gig = None
        else:
            the_gig = ndb.Key(urlsafe=the_gig_key).get()

        edit_date_change = False
        edit_time_change = False
        edit_status_change = False
        edit_detail_change = False

        # first, get the band
        gig_is_new = False
        gig_band_keyurl = self.request.get("gig_band", None)
        if gig_band_keyurl is not None and gig_band_keyurl != '':
            the_band = ndb.Key(urlsafe=gig_band_keyurl).get()
            if the_gig is None:
                the_gig = new_gig(title="tmp", the_band=the_band, creator=self.user.key)
                gig_is_new = True

        # are we authorized to edit a gig for this band?
        ok_band_list = self.user.get_add_gig_band_list(self, self.user.key)
        if not the_band.key in [x.key for x in ok_band_list]:
            logging.error(u'user {0} trying to edit a gig for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))
            return self.redirect('/')            

        # now get the info
        gig_title = self.request.get("gig_title", None)
        if gig_title is not None and gig_title != '':
            the_gig.title = gig_title
        
        gig_contact = self.request.get("gig_contact", None)
        if gig_contact is not None and gig_contact != '':
            the_gig.contact = ndb.Key(urlsafe=gig_contact)
        
        gig_details = self.request.get("gig_details", None)
        if gig_details is not None:
            the_gig.details = gig_details

        gig_setlist = self.request.get("gig_setlist", None)
        if gig_setlist is not None:
            the_gig.setlist = gig_setlist

        gig_rssdescription = self.request.get("gig_rssdescription", None)
        if gig_rssdescription is not None:
            the_gig.rss_description = gig_rssdescription

        gig_date = self.request.get("gig_date", None)
        if gig_date is not None and gig_date != '':
            old_date = the_gig.date
            the_gig.date = datetime.datetime.combine(babel.dates.parse_date(gig_date,locale=self.user.preferences.locale),datetime.time(0,0,0))
            if old_date != the_gig.date:
                edit_date_change = True
                
        # todo validate form entry so date isn't bogus
       
        gig_enddate = self.request.get("gig_enddate", None)
        old_enddate = the_gig.enddate
        if gig_enddate is not None and gig_enddate != '':
            the_gig.enddate = datetime.datetime.combine(babel.dates.parse_date(gig_enddate,locale=self.user.preferences.locale),datetime.time(0,0,0))
        else:
            the_gig.enddate = None
        if old_enddate != the_gig.enddate:
            edit_date_change = True

        gig_call = self.request.get("gig_call", '')
        if gig_call is not None:
            if the_gig.calltime != gig_call:
                the_gig.set_calltime(gig_call)
                edit_time_change = True

        gig_set = self.request.get("gig_set", '')
        if gig_set is not None:
            if the_gig.settime != gig_set:
                the_gig.set_settime(gig_set)
                edit_time_change = True

        gig_end = self.request.get("gig_end", '')
        if gig_end is not None:
            if the_gig.endtime != gig_end:
                the_gig.set_endtime(gig_end)
                edit_time_change = True

        gig_address = self.request.get("gig_address", '')
        if gig_address is not None:
            the_gig.address = gig_address

        gig_dress = self.request.get("gig_dress", '')
        if gig_dress is not None:
            the_gig.dress = gig_dress

        gig_paid = self.request.get("gig_paid", '')
        if gig_paid is not None:
            the_gig.paid = gig_paid

        gig_leader = self.request.get("gig_leader", '')
        if gig_leader is not None:
            the_gig.leader = gig_leader
        
        gig_postgig = self.request.get("gig_postgig", '')
        if gig_postgig is not None:
            the_gig.postgig = gig_postgig

        gig_status = self.request.get("gig_status", '0')
        old_status = the_gig.status
        the_gig.status = int(gig_status)
        if old_status != the_gig.status:
            edit_status_change = True

        gig_invite_occasionals=self.request.get("gig_invite_occasionals",None)
        if (gig_invite_occasionals):
            the_gig.invite_occasionals = True
        else:
            the_gig.invite_occasionals = False

        gig_hide_from_calendar=self.request.get("gig_hide_from_calendar",None)
        if (gig_hide_from_calendar):
            the_gig.hide_from_calendar = True
        else:
            the_gig.hide_from_calendar = False


        gig_private=self.request.get("gig_private",None)
        if (gig_private):
            the_gig.is_private = True
        else:
            the_gig.is_private = False

        gig_default_to_attending = self.request.get("default_to_attend",None)
        if (gig_default_to_attending):
            logging.info("\n\nattending!\n\n")
            the_gig.default_to_attending = True

        the_gig.put()

        # Is this a series?
        is_series = self.request.get("newgig_isseries", False)
        if is_series:
            number_to_copy = int(self.request.get("newgig_seriescount",1)) - 1
            period = self.request.get("newgig_seriesperiod",None)
            
            last_date = the_gig.date
            if period == 'day':
                delta = datetime.timedelta(days=1)
            elif period == 'week':
                delta = datetime.timedelta(weeks=1)
            else:
                day_of_month = last_date.day
                
            if the_gig.enddate:
                end_delta = the_gig.enddate - the_gig.date
            else:
                end_delta = None

            newgigs=[]                
            for i in range(0,number_to_copy):
                copy_gig = clone_entity(the_gig,Gig)
                if period == 'day' or period == 'week':
                    last_date = last_date + delta
                else:
                    # figure out what the next month is
                    if last_date.month< 12:
                        mo = last_date.month+1
                        yr = last_date.year
                    else:
                        mo = 1
                        yr = last_date.year+1
                    # figure out last day of next month
                    nextmonth = last_date.replace(month=mo, day=1, year=yr)
                    nextnextmonth = (nextmonth + datetime.timedelta(days=35)).replace(day=1)
                    lastday=(nextnextmonth - datetime.timedelta(days=1)).day
                    if lastday < day_of_month:
                        day_of_gig = lastday
                    else:
                        day_of_gig = day_of_month
                    last_date = last_date.replace(month=mo, day=day_of_gig, year=yr)
                copy_gig.date = last_date
                
                if end_delta is not None:
                    copy_gig.enddate = copy_gig.date + end_delta

                newgigs.append(copy_gig)

            if newgigs:
                ndb.put_multi(newgigs)

        gig_notify = self.request.get("gig_notifymembers", None)

        if gig_notify is not None:
            if gig_is_new:
                goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=False)
            else:
                if edit_time_change or edit_date_change or edit_status_change:
                    change_strings=[]
                    if edit_time_change:
                        change_strings.append(_('Time'))
                    if edit_date_change:
                        change_strings.append(_('Date'))
                    if edit_status_change:
                        change_strings.append(_('Status'))
                    change_str = ', '.join(change_strings)
                else:
                    change_str = _('Details')
                goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=True, change_string=change_str)

        if (the_band.rss_feed):
            rss.make_rss_feed_for_band(the_band)

        band.make_band_cal_dirty(the_band)

        return self.redirect(\
            '/gig_info.html?&gk={0}'.format(the_gig.key.urlsafe()))
                
class DeleteHandler(BaseHandler):

    @user_required
    def get(self):

        user = self.user
        
        the_gig_key = self.request.get("gk", None)

        if the_gig_key is None:
            raise gigoexceptions.GigoException('deletehandler did not find a gig in the request')
        else:
            the_gig = ndb.Key(urlsafe=the_gig_key).get()
            if the_gig:
                the_gig.trashed_date = datetime.datetime.now()
                the_gig.put()
        return self.redirect('/')
            
class RestoreHandler(BaseHandler):

    @user_required
    def get(self):

        user = self.user
        
        the_gig_key = self.request.get("gk", None)

        if the_gig_key is None:
            raise gigoexceptions.GigoException('restore did not find a gig in the request')
        else:
            the_gig = ndb.Key(urlsafe=the_gig_key).get()
            if the_gig:
                the_gig.trashed_date = None
                the_gig.put()
        return self.redirect(\
            '/gig_info.html?&gk={0}'.format(the_gig.key.urlsafe()))

class PrintSetlist(BaseHandler):
    """ print-friendly setlist view """
    
    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        the_gig_keyurl = self.request.get("gk", '0')
        
        if (the_gig_keyurl == '0'):
            return # todo what else to do?
        else:
            the_gig = ndb.Key(urlsafe=the_gig_keyurl).get()

        template_args = {
            'the_gig' : the_gig,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('print_setlist.html', template_args)
        
class PrintPlanlist(BaseHandler):
    """ print-friendly list of member plans """
    
    @user_required
    def get(self):
        self._make_page(self.user)
    
    def _make_page(self, the_user):
        the_gig_keyurl = self.request.get("gk", '0')
        the_printall = self.request.get("printall", '1')
        
        if (the_gig_keyurl == '0'):
            return # todo what else to do?
        else:
            the_gig_key = ndb.Key(urlsafe=the_gig_keyurl)
            
        the_gig = the_gig_key.get()   
        the_band_key = the_gig_key.parent()

        the_assocs = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=True, keys_only=False)

        the_plans = []
    
        if the_printall=='1':
            printall = True
        else:
            printall = False

        need_empty_section = False
        for the_assoc in the_assocs:
            a_member_key = the_assoc.member
            the_plan = plan.get_plan_for_member_key_for_gig_key(a_member_key, the_gig_key)
            if the_plan.section==None and the_assoc.default_section==None:
                need_empty_section = True
            info_block={}
            info_block['the_gig_key'] = the_gig.key
            info_block['the_plan_key'] = the_plan.key
            info_block['the_member_key'] = a_member_key
            info_block['the_band_key'] = the_band_key
            info_block['the_assoc'] = the_assoc
            if the_plan.section is not None:
                info_block['the_section'] = the_plan.section
            else:
                info_block['the_section'] = the_assoc.default_section            
            
            the_plans.append(info_block)          
    
        the_section_keys = band.get_section_keys_of_band_key(the_band_key)
        if need_empty_section:
            the_section_keys.append(None)            

        template_args = {
            'the_gig' : the_gig,
            'the_plans' : the_plans,
            'the_section_keys' : the_section_keys,
            'printall' : printall
        }
        self.render_template('print_planlist.html', template_args)
        
            
        
class ArchiveHandler(BaseHandler):
    """ archive this gig, baby! """
            
    @user_required
    def get(self):

        # find the gig we're interested in
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            self.response.write('no gig key passed in!')
            return # todo figure out what to do if there's no ID passed in
            
        the_gig_key=ndb.Key(urlsafe=gig_key_str)
        if the_gig_key:
            make_archive_for_gig_key(the_gig_key)

        return self.redirect('/gig_info.html?gk={0}'.format(gig_key_str))

def _do_autoarchive():
    date = datetime.datetime.now()
    end_date = date - datetime.timedelta(days=3)
    the_gig_keys = get_old_gig_keys(end_date = end_date)
    for a_gig_key in the_gig_keys:
        make_archive_for_gig_key(a_gig_key)
    logging.info("Archived {0} gigs".format(len(the_gig_keys)))

    # while we're here, look for gigs that have been trashed more than 30 days ago
    gigs = get_old_trashed_gigs(minimum_age=30)
    logging.info("Deleting {0} trashed gigs".format(len(gigs)))
    for g in gigs:
        delete_gig_completely(g)

        
class AutoArchiveHandler(BaseHandler):
    """ automatically archive old gigs """
    def get(self):
        _do_autoarchive()
        
class CommentHandler(BaseHandler):
    """ takes a new comment and adds it to the gig """

    @user_required
    def post(self):
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in

        the_gig_key = ndb.Key(urlsafe=gig_key_str)
#         the_gig = the_gig_key.get()

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str=='':
            return

#   OLD COMMENT HANDLING        
#         dt=datetime.datetime.now()
# 
#         offset_str = self.request.get("o", None)
#         if comment_str is not None:
#             offset=int(offset_str)
#             dt = dt - datetime.timedelta(hours=offset)
# 
#         user=self.user
#         timestr=dt.strftime('%-m/%-d/%Y %I:%M%p')
#         new_comment = u'{0} ({1}) said at {2}:\n{3}'.format(user.name, user.email_address, timestr, comment_str)
# 
#         new_id, the_comment_text = gigcomment.add_comment_for_gig(new_comment, the_gig.comment_id)
#         if new_id != the_gig.comment_id:
#             the_gig.comment_id = new_id
#             the_gig.put()
# 
#         self.response.write(jinja2ext.html_content(the_comment_text))

        comment.new_comment(the_gig_key, self.user.key, comment_str)
        self.response.write('')        

class GetCommentHandler(BaseHandler):
    """ returns the comment for a gig if there is one """
    
    @user_required
    def post(self):
    
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig = ndb.Key(urlsafe=gig_key_str).get()

        # first, get the old comment text if there is any
        if the_gig.comment_id:
            the_old_comment = gigcomment.get_comment(the_gig.comment_id)
        else:
            the_old_comment = None

        new_comments = comment.get_comments_from_gig_key(the_gig.key)
        
        template_args = {
            'the_old_comments' : the_old_comment,
            'the_comments' : new_comments,
            'the_date_formatter' : member.format_date_for_member            
        }
        
        self.render_template('comments.html', template_args)
        

class AnswerLinkHandler(BaseHandler):
    """ special url handler for encoded user, gig, answer links """
    
    def get(self):
        answer_str = self.request.get("c", None)
        if answer_str is None:
            return # todo figure out what to do if there's no ID passed in
            
        code = cryptoutil.decrypt_string(answer_str).strip()
        
        parts=code.split('+')
        
        member_key = ndb.Key(urlsafe=parts[0])
        gig_key = ndb.Key(urlsafe=parts[1])
        the_plan = plan.get_plan_for_member_key_for_gig_key(member_key, gig_key)
        if the_plan:
            if parts[2] == '0':
                plan.update_plan(the_plan,5)
            elif parts[2] == '1':
                plan.update_plan(the_plan,1)
            elif parts[2] == '2':
                plan.update_plan(the_plan,3)
                # snooze!
                the_gig = the_plan.key.parent().get()
                snooze_days = 7
                gig_future = the_gig.date - datetime.datetime.now()
                if gig_future.days < 8:
                    snooze_days = gig_future.days - 2

                if snooze_days > 0:
                    snooze_day = datetime.datetime.now() + datetime.timedelta(days = snooze_days)
                    # logging.info("\n\nsnooze date is {0}\n\n".format(snooze_day))
                    the_plan.snooze_until = snooze_day
                    the_plan.put()
                    # TODO if the gig is too soon, silently ignore request fo snooze - should give a message

            else:
                logging.error("answerlink got unknown type.\ngig key:{0}\nmember_key:{1}".format(parts[1], parts[0]))
        
            self.render_template('confirm_answer.html', [])
        else:
            logging.error("answer link failed.\ngig key:{0}\nmember_key:{1}".format(parts[1], parts[0]))
            self.render_template('error.html', [])

class SendReminder(BaseHandler):
    """ special URL to send a reminder email to straggler members for a gig """

    def post(self):
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig = ndb.Key(urlsafe=gig_key_str).get()

        the_plans = plan.get_plans_for_gig_key(the_gig.key)

        stragglers=[]
        for p in the_plans:
            if p.value in [0,3]:
                stragglers.append(p.member)

        if len(stragglers) > 0:
            goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=False, is_reminder=True, the_members=stragglers)


        # OK, we sent the reminder.
        the_gig.was_reminded = True
        the_gig.put()

##########
#
# REST endpoint stuff
#
##########

def _RestGigInfo(the_gig, include_id=True):
    obj = { k:getattr(the_gig,k) for k in ('title','details','setlist','date','calltime','settime',
                                            'endtime','address','paid','dress','leader','postgig','status','is_in_trash') }
    obj['contact'] = the_gig.contact.urlsafe() if the_gig.contact else ""
    obj['band'] = the_gig.key.parent().urlsafe()
    if include_id:
        obj['id'] = the_gig.key.urlsafe()
    return obj


class RestEndpoint(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self, *args, **kwargs):
        try:
            gig_id = kwargs["gig_id"]
            the_gig = ndb.Key(urlsafe=gig_id).get()
        except:
            self.abort(404)

        # are we authorized to see the gig?
        if assoc.get_assoc_for_band_key_and_member_key(self.user.key, the_gig.key.parent(), confirmed_only=False) is None:
            self.abort(401)

        return _RestGigInfo(the_gig, include_id=False)

def _RestGigPlanInfo(the_plans):
    member_keys = [i['the_member_key'] for i in the_plans]
    members = ndb.get_multi(member_keys)
    member_names = dict(zip(member_keys,[m.display_name for m in members]))

    plans = []
    for info_block in the_plans:
        info = {}
        info['the_plan'] = plan._RestPlanInfo(info_block['the_plan'])
        info['the_member_key'] = info_block['the_member_key'].urlsafe()
        info['the_member_name'] = member_names[info_block['the_member_key']]
        if info['the_plan']['section'] == '':
            if info_block['the_assoc'].default_section:
                info['the_plan']['section'] = info_block['the_assoc'].default_section.urlsafe()
        plans.append(info)
    return plans

class RestEndpointPlans(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self, *args, **kwargs):
        try:
            gig_id = kwargs["gig_id"]
            the_gig = ndb.Key(urlsafe=gig_id).get()
        except:
            self.abort(404)

        # are we authorized to see the gig?
        if assoc.get_assoc_for_band_key_and_member_key(self.user.key, the_gig.key.parent(), confirmed_only=False) is None:
            self.abort(401)

        the_band_key = the_gig.key.parent()
        the_plans, the_plan_counts, the_sections, band_has_sections = _makeInfoPageInfo(self.user, the_gig, the_band_key)

        return _RestGigPlanInfo(the_plans)
