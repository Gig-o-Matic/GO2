"""

 gig class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb
from requestmodel import *
from restify import rest_user_required, CSOR_Jsonify

import member
import band
import gig
import goemail
import gigarchive
import gigcomment
import assoc
import comment
import plan
import cryptoutil
import rss
import logging
import gigoexceptions
import clone

from webapp2_extras.i18n import gettext as _

from clone import clone_entity

import datetime
import babel


#
#
# routines for turning gig into info for REST api
#
#


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

        gig_key = gig.gig_key_from_urlsafe(gig_key_str)
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
            user_can_edit = gig.can_edit_gig(the_user, the_gig, the_band)
            user_can_create = gig.can_edit_gig(the_user, None, the_band)

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
                the_band = band.band_key_from_urlsafe(the_band_keyurl).get()
        else:
            the_gig_key = self.request.get("gk", None)
            if (the_gig_key is None):
                return # figure out what to do
                
            the_gig = gig.get_gig_from_key(gig.gig_key_from_urlsafe(the_gig_key))
            if the_gig is None:
                self.response.write('did not find a band or gig!')
                return # todo figure out what to do if we didn't find it
            is_new = False
            the_band = the_gig.key.parent().get()

        # are we authorized to edit this gig?
        if gig.can_edit_gig(self.user, the_gig, the_band) is False:
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
            the_gig = gig.gig_key_from_urlsafe(the_gig_key).get()

        edit_date_change = False
        edit_time_change = False
        edit_status_change = False
        edit_detail_change = False

        # first, get the band
        gig_is_new = False
        gig_band_keyurl = self.request.get("gig_band", None)
        if gig_band_keyurl is not None and gig_band_keyurl != '':
            the_band = band.band_key_from_urlsafe(gig_band_keyurl).get()
            if the_gig is None:
                the_gig = gig.new_gig(title="tmp", the_band=the_band, creator=self.user.key)
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
            the_gig.contact = member.member_key_from_urlsafe(gig_contact)
        
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
            for i in range(0, number_to_copy):
                copy_gig = clone.clone_entity(the_gig, gig.Gig)
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
            the_gig = gig.gig_key_from_urlsafe(the_gig_key).get()
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
            the_gig = gig.gig_key_from_urlsafe(the_gig_key).get()
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
            the_gig = gig.gig_key_from_urlsafe(the_gig_keyurl).get()

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
            the_gig_key = gig.gig_key_from_urlsafe(the_gig_keyurl)
            
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
            
        the_gig_key = gig.gig_key_from_urlsafe(gig_key_str)
        if the_gig_key:
            gig.make_archive_for_gig_key(the_gig_key)

        return self.redirect('/gig_info.html?gk={0}'.format(gig_key_str))

def _do_autoarchive():
    date = datetime.datetime.now()
    end_date = date - datetime.timedelta(days=3)
    the_gig_keys = gig.get_old_gig_keys(end_date = end_date)
    for a_gig_key in the_gig_keys:
        gig.make_archive_for_gig_key(a_gig_key)
    logging.info("Archived {0} gigs".format(len(the_gig_keys)))

    # while we're here, look for gigs that have been trashed more than 30 days ago
    gigs = gig.get_old_trashed_gigs(minimum_age=30)
    logging.info("Deleting {0} trashed gigs".format(len(gigs)))
    for g in gigs:
        gig.delete_gig_completely(g)

        
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

        the_gig_key = gig.gig_key_from_urlsafe(gig_key_str)

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str=='':
            return

        comment.new_comment(the_gig_key, self.user.key, comment_str)
        self.response.write('')        

class GetCommentHandler(BaseHandler):
    """ returns the comment for a gig if there is one """
    
    @user_required
    def post(self):
    
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig = gig.gig_key_from_urlsafe(gig_key_str).get()

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
        
        member_key = member.member_key_from_urlsafe(parts[0])
        gig_key = gig.gig_key_from_urlsafe(parts[1])
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
        the_gig = gig.gig_key_from_urlsafe(gig_key_str).get()

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


class RestEndpoint(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self, *args, **kwargs):
        try:
            gig_id = kwargs["gig_id"]
            the_gig = gig.gig_key_from_urlsafe(gig_id).get()
        except:
            self.abort(404)

        # are we authorized to see the gig?
        if assoc.get_assoc_for_band_key_and_member_key(self.user.key, the_gig.key.parent(), confirmed_only=False) is None:
            self.abort(401)

        return gig.rest_gig_info(the_gig, include_id=False)


class RestEndpointPlans(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self, *args, **kwargs):
        try:
            gig_id = kwargs["gig_id"]
            the_gig = gig.gig_key_from_urlsafe(gig_id).get()
        except:
            self.abort(404)

        # are we authorized to see the gig?
        if assoc.get_assoc_for_band_key_and_member_key(self.user.key, the_gig.key.parent(), confirmed_only=False) is None:
            self.abort(401)

        the_band_key = the_gig.key.parent()
        the_plans, the_plan_counts, the_sections, band_has_sections = _makeInfoPageInfo(self.user, the_gig, the_band_key)

        return gig.rest_gig_plan_info(the_plans)
