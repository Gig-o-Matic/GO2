"""

 poll class for Gig-o-Matic 2 

 Aaron Oppenheimer
 1 September 2019

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
# Handlers
#
#

def _makeInfoPageInfo(the_user, the_poll, the_band_key):
    poll_key = the_poll.key

    the_assocs = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=True, keys_only=False)
    
    # get all the plans for this poll - might actually not be any yet.
    all_plans = plan.get_plans_for_gig_key(poll_key, keys_only=False)
    
    # now, for each associated member, find or make a plan
    the_new_plans = [] # in case we need to make new ones

    the_plan_counts={}
    for i in range(len(the_poll.setlist.split('\n'))+1):
        the_plan_counts[i]=0

    for the_assoc in the_assocs:
        a_member_key = the_assoc.member
        new_plan = False
        
        for p in all_plans:
            if p.member == a_member_key:
                the_plan = p
                break
        else:
            # no plan? make a new one
            the_plan = plan.Plan(parent=poll_key, member=a_member_key, value=0, comment="", section=None)
            the_plan.feedback_value=0
            the_new_plans.append(the_plan)
            new_plan = True

        the_plan_counts[the_plan.feedback_value] += 1

    if the_new_plans:
        ndb.put_multi(the_new_plans)

    return the_plan_counts


class InfoPage(BaseHandler):
    """ class to serve the poll info page """

    @user_required
    def get(self):    
        self._make_page(self.user)

    def _make_page(self, the_user):

        # find the poll we're interested in
        poll_key_str = self.request.get("pk", None)
        if poll_key_str is None:
            raise gigoexceptions.GigoException('no poll key passed in!')

        poll_key = gig.gig_key_from_urlsafe(poll_key_str)
        the_poll = poll_key.get()

        if the_poll is None:
            template_args = {}
            raise gigoexceptions.GigoException('no poll found!')

        the_comment_text = None
        if the_poll.comment_id:
            the_comment_text = gigcomment.get_comment(the_poll.comment_id)

        if not the_poll.is_archived:

            the_band_key = the_poll.key.parent()
            the_answer_counts = _makeInfoPageInfo(the_user, the_poll, the_band_key)

            # get this user's plan
            user_plan = plan.get_plan_for_member_key_for_gig_key(the_user.key, the_poll.key, keys_only=False)

            # is the current user a band admin?
            the_user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key)
            user_can_edit = the_user_is_band_admin or the_user.is_superuser

            datestr = member.format_date_for_member(the_user, the_poll.date, format="long")

            template_args = {
                'poll' : the_poll,
                'date_str' : datestr,
                'comment_text' : the_comment_text,
                'the_user_is_band_admin' : the_user_is_band_admin,
                'user_can_edit' : user_can_edit,
                'the_answer_counts' : the_answer_counts,
                'the_answers' : the_poll.setlist.split('\n'),
                'user_plan' : user_plan
            }
            self.render_template('poll_info.html', template_args)
        # else:
        #     # this is an archived poll
        #     the_archived_plans = gigarchive.get_archived_plans(the_poll.archive_id)
        #     template_args = {
        #         'poll' : the_poll,
        #         'archived_plans' : the_archived_plans,
        #         'comment_text' : the_comment_text
        #     }
        #     self.render_template('poll_archived_info.html', template_args)
      


class EditPage(BaseHandler):
    """ A class for rendering the gig edit page """

    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        if self.request.get("new", None) is not None:
            the_poll = None
            is_new = True
            
            the_band_keyurl = self.request.get("bk", None)
            if the_band_keyurl is None:
                return # figure out what to do
            else:
                the_band = band.band_key_from_urlsafe(the_band_keyurl).get()
        else:
            the_poll_key = self.request.get("pk", None)
            if (the_poll_key is None):
                return # figure out what to do
                
            the_poll = gig.get_gig_from_key(gig.gig_key_from_urlsafe(the_poll_key))
            if the_poll is None:
                self.response.write('did not find a band or poll!')
                return # todo figure out what to do if we didn't find it
            is_new = False
            the_band = the_poll.key.parent().get()

        # are we authorized to edit this poll?
        if gig.can_edit_gig(self.user, the_poll, the_band) is False:
            # logging.error(u'user {0} trying to edit a poll for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))
            raise gigoexceptions.GigoException('user {0} trying to edit a poll for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))
            
        template_args = {
            'poll' : the_poll,
            'the_band' : the_band,
            'newpoll_is_active' : is_new,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('poll_edit.html', template_args)
        
    @user_required        
    def post(self):
        """post handler - if we are edited by the template, handle it here 
           and redirect back to info page"""

        the_poll_key = self.request.get("pk", '0')
        
        if (the_poll_key == '0'):
            the_poll = None
        else:
            # polls are just gigs
            the_poll = gig.gig_key_from_urlsafe(the_poll_key).get()

        edit_date_change = False
        edit_status_change = False
        edit_detail_change = False

        # first, get the band
        poll_is_new = False
        poll_band_keyurl = self.request.get("poll_band", None)
        if poll_band_keyurl is not None and poll_band_keyurl != '':
            the_band = band.band_key_from_urlsafe(poll_band_keyurl).get()
            if the_poll is None:
                the_poll = gig.new_gig(title="tmp", the_band=the_band, creator=self.user.key, status=gig.Gig.poll_status['open'])
                gig_is_new = True

        # are we authorized to edit a poll for this band?
        ok_band_list = self.user.get_add_gig_band_list(self, self.user.key)
        if not the_band.key in [x.key for x in ok_band_list]:
            logging.error(u'user {0} trying to edit a poll for band {1}'.format(self.user.key.urlsafe(),the_band.key.urlsafe()))
            return self.redirect('/')            

        # now get the info
        poll_title = self.request.get("poll_title", None)
        if poll_title is not None and poll_title != '':
            the_poll.title = poll_title
        
        poll_details = self.request.get("poll_details", None)
        if poll_details is not None:
            the_poll.details = poll_details

        poll_answers = self.request.get("poll_answers", None)
        if poll_answers is not None:
            the_poll.setlist = poll_answers

        poll_date = self.request.get("poll_date", None)
        if poll_date is not None and poll_date != '':
            old_date = the_poll.date
            the_poll.date = datetime.datetime.combine(babel.dates.parse_date(poll_date,locale=self.user.preferences.locale),datetime.time(0,0,0))
            if old_date != the_poll.date:
                edit_date_change = True

        # gig_status = self.request.get("gig_status", '0')
        # old_status = the_gig.status
        # the_gig.status = int(gig_status)
        # if old_status != the_gig.status:
        #     edit_status_change = True

        poll_invite_occasionals=self.request.get("poll_invite_occasionals",None)
        if (poll_invite_occasionals):
            the_poll.invite_occasionals = True
        else:
            the_poll.invite_occasionals = False

        the_poll.put()

        poll_notify = self.request.get("poll_notifymembers", None)

        # if poll_notify is not None:
        #     if poll_is_new:
        #         goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=False)
        #     else:
        #         if edit_time_change or edit_date_change or edit_status_change:
        #             change_strings=[]
        #             if edit_time_change:
        #                 change_strings.append(_('Time'))
        #             if edit_date_change:
        #                 change_strings.append(_('Date'))
        #             if edit_status_change:
        #                 change_strings.append(_('Status'))
        #             change_str = ', '.join(change_strings)
        #         else:
        #             change_str = _('Details')
        #         goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=True, change_string=change_str)

        return self.redirect(\
            '/poll_info.html?&pk={0}'.format(the_poll.key.urlsafe()))
                
# class DeleteHandler(BaseHandler):
#     @user_required
#     def get(self):

#         user = self.user
        
#         the_gig_key = self.request.get("gk", None)

#         if the_gig_key is None:
#             raise gigoexceptions.GigoException('deletehandler did not find a gig in the request')
#         else:
#             the_gig = gig.gig_key_from_urlsafe(the_gig_key).get()
#             if the_gig:
#                 the_gig.trashed_date = datetime.datetime.now()
#                 the_gig.put()
#         return self.redirect('/')
            
# class RestoreHandler(BaseHandler):

#     @user_required
#     def get(self):

#         user = self.user
        
#         the_gig_key = self.request.get("gk", None)

#         if the_gig_key is None:
#             raise gigoexceptions.GigoException('restore did not find a gig in the request')
#         else:
#             the_gig = gig.gig_key_from_urlsafe(the_gig_key).get()
#             if the_gig:
#                 the_gig.trashed_date = None
#                 the_gig.put()
#         return self.redirect(\
#             '/gig_info.html?&gk={0}'.format(the_gig.key.urlsafe()))


# class ArchiveHandler(BaseHandler):
#     """ archive this gig, baby! """
            
#     @user_required
#     def get(self):

#         # find the gig we're interested in
#         gig_key_str = self.request.get("gk", None)
#         if gig_key_str is None:
#             self.response.write('no gig key passed in!')
#             return # todo figure out what to do if there's no ID passed in
            
#         the_gig_key = gig.gig_key_from_urlsafe(gig_key_str)
#         if the_gig_key:
#             gig.make_archive_for_gig_key(the_gig_key)

#         return self.redirect('/gig_info.html?gk={0}'.format(gig_key_str))

# def _do_autoarchive():
#     date = datetime.datetime.now()
#     end_date = date - datetime.timedelta(days=3)
#     the_gig_keys = gig.get_old_gig_keys(end_date = end_date)
#     for a_gig_key in the_gig_keys:
#         gig.make_archive_for_gig_key(a_gig_key)
#     logging.info("Archived {0} gigs".format(len(the_gig_keys)))

#     # while we're here, look for gigs that have been trashed more than 30 days ago
#     gigs = gig.get_old_trashed_gigs(minimum_age=30)
#     logging.info("Deleting {0} trashed gigs".format(len(gigs)))
#     for g in gigs:
#         gig.delete_gig_completely(g)

        
# class AutoArchiveHandler(BaseHandler):
#     """ automatically archive old gigs """
#     def get(self):
#         _do_autoarchive()
        
# class CommentHandler(BaseHandler):
#     """ takes a new comment and adds it to the gig """

#     @user_required
#     def post(self):
#         gig_key_str = self.request.get("gk", None)
#         if gig_key_str is None:
#             return # todo figure out what to do if there's no ID passed in

#         the_gig_key = gig.gig_key_from_urlsafe(gig_key_str)

#         comment_str = self.request.get("c", None)
#         if comment_str is None or comment_str=='':
#             return

#         comment.new_comment(the_gig_key, self.user.key, comment_str)
#         self.response.write('')        

# class GetCommentHandler(BaseHandler):
#     """ returns the comment for a gig if there is one """
    
#     @user_required
#     def post(self):
    
#         gig_key_str = self.request.get("gk", None)
#         if gig_key_str is None:
#             return # todo figure out what to do if there's no ID passed in
#         the_gig = gig.gig_key_from_urlsafe(gig_key_str).get()

#         # first, get the old comment text if there is any
#         if the_gig.comment_id:
#             the_old_comment = gigcomment.get_comment(the_gig.comment_id)
#         else:
#             the_old_comment = None

#         new_comments = comment.get_comments_from_gig_key(the_gig.key)
        
#         template_args = {
#             'the_old_comments' : the_old_comment,
#             'the_comments' : new_comments,
#             'the_date_formatter' : member.format_date_for_member            
#         }
        
#         self.render_template('comments.html', template_args)
        

# class AnswerLinkHandler(BaseHandler):
#     """ special url handler for encoded user, gig, answer links """
    
#     def get(self):
#         answer_str = self.request.get("c", None)
#         if answer_str is None:
#             return # todo figure out what to do if there's no ID passed in
            
#         code = cryptoutil.decrypt_string(answer_str).strip()
        
#         parts=code.split('+')
        
#         member_key = member.member_key_from_urlsafe(parts[0])
#         gig_key = gig.gig_key_from_urlsafe(parts[1])
#         the_plan = plan.get_plan_for_member_key_for_gig_key(member_key, gig_key)
#         if the_plan:
#             if parts[2] == '0':
#                 plan.update_plan(the_plan,5)
#             elif parts[2] == '1':
#                 plan.update_plan(the_plan,1)
#             elif parts[2] == '2':
#                 plan.update_plan(the_plan,3)
#                 # snooze!
#                 the_gig = the_plan.key.parent().get()
#                 snooze_days = 7
#                 gig_future = the_gig.date - datetime.datetime.now()
#                 if gig_future.days < 8:
#                     snooze_days = gig_future.days - 2

#                 if snooze_days > 0:
#                     snooze_day = datetime.datetime.now() + datetime.timedelta(days = snooze_days)
#                     # logging.info("\n\nsnooze date is {0}\n\n".format(snooze_day))
#                     the_plan.snooze_until = snooze_day
#                     the_plan.put()
#                     # TODO if the gig is too soon, silently ignore request fo snooze - should give a message

#             else:
#                 logging.error("answerlink got unknown type.\ngig key:{0}\nmember_key:{1}".format(parts[1], parts[0]))
        
#             self.render_template('confirm_answer.html', [])
#         else:
#             logging.error("answer link failed.\ngig key:{0}\nmember_key:{1}".format(parts[1], parts[0]))
#             self.render_template('error.html', [])

# class SendReminder(BaseHandler):
#     """ special URL to send a reminder email to straggler members for a gig """

#     def post(self):
#         gig_key_str = self.request.get("gk", None)
#         if gig_key_str is None:
#             return # todo figure out what to do if there's no ID passed in
#         the_gig = gig.gig_key_from_urlsafe(gig_key_str).get()

#         the_plans = plan.get_plans_for_gig_key(the_gig.key)

#         stragglers=[]
#         for p in the_plans:
#             if p.value in [0,3]:
#                 stragglers.append(p.member)

#         if len(stragglers) > 0:
#             goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()), is_edit=False, is_reminder=True, the_members=stragglers)


#         # OK, we sent the reminder.
#         the_gig.was_reminded = True
#         the_gig.put()

