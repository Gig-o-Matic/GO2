import webapp2
from google.appengine.api import users
from google.appengine.api.taskqueue import taskqueue

import gig
import member
import assoc
import logging
import pickle

from webapp2_extras import i18n
from webapp2_extras.i18n import gettext as _

def announce_gig(the_gig, the_gig_url, is_edit=False, is_reminder=False, change_string="", the_members=[]):
    the_params = pickle.dumps({'the_gig_key':   the_gig.key,
                               'the_gig_url':   the_gig_url,
                               'is_edit':       is_edit,
                               'is_reminder':   is_reminder,
                               'change_string': change_string,
                               'the_members':   the_members})

    taskqueue.add(
            url='/announce_gig_handler',
            params={'the_params': the_params
            })

def queue_gig_member_email(an_assoc, the_shared_params):
    if an_assoc.email_me:
        the_member_key = an_assoc.member

        the_member_params = pickle.dumps({
            'the_member_key': the_member_key
        })

        task = taskqueue.add(
            queue_name='emailqueue',
            url='/email_gig_handler',
            params={'the_shared_params': the_shared_params,
                    'the_member_params': the_member_params
            })

def queue_gig_slack_message(the_shared_params):
        task = taskqueue.add(
            queue_name='slackqueue',
            url='/slack_gig_handler',
            params={'the_shared_params': the_shared_params}
        )

def format_date_string(the_date, the_member):
    return "{0} ({1})".format(member.format_date_for_member(the_member, the_date),
                              member.format_date_for_member(the_member, the_date, "day"))

def format_time_string(the_gig):
    the_time_string = ""
    if the_gig.calltime:
        the_time_string = u'{0} ({1})'.format(the_gig.calltime, _('Call Time'))
    if the_gig.settime:
        if the_time_string:
            the_time_string = u'{0}, '.format(the_time_string)
        the_time_string = u'{0}{1} ({2})'.format(the_time_string,the_gig.settime, _('Set Time'))
    if the_gig.endtime:
        if the_time_string:
            the_time_string = u'{0}, '.format(the_time_string)
        the_time_string = u'{0}{1} ({2})'.format(the_time_string,the_gig.endtime, _('End Time'))
    return the_time_string

class AnnounceGigHandler(webapp2.RequestHandler):

    def post(self):
        the_params = pickle.loads(self.request.get('the_params'))

        the_gig_key  = the_params['the_gig_key']
        the_gig_url = the_params['the_gig_url']
        is_edit = the_params['is_edit']
        is_reminder = the_params['is_reminder']
        change_string = the_params['change_string']
        the_members = the_params['the_members']

        the_gig = the_gig_key.get()
        the_band_key = the_gig_key.parent()
        the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band_key, include_occasional=the_gig.invite_occasionals)

        if is_reminder and the_members:
            recipient_assocs=[]
            for a in the_assocs:
                if a.member in the_members:
                    recipient_assocs.append(a)
        else:
            recipient_assocs = the_assocs

        logging.info('announcing gig {0} to {1} people'.format(the_gig_key,len(recipient_assocs)))

        the_shared_params = pickle.dumps({
            'the_gig_key': the_gig_key,
            'the_band_key': the_band_key,
            'the_gig_url': the_gig_url,
            'is_edit': is_edit,
            'is_reminder': is_reminder,
            'change_string': change_string
        })

        the_band = the_band_key.get()
        if the_band.slack_bot_access_token:
            queue_gig_slack_message(the_shared_params)

        for an_assoc in recipient_assocs:
            queue_gig_member_email(an_assoc, the_shared_params)

        logging.info('announced gig {0}'.format(the_gig_key))

        self.response.write( 200 )
