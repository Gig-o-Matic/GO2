import webapp2
from google.appengine.ext import ndb

import logging
import pickle
import os

import slack_client
from slack_client import SlackClient
import assoc
import band
import gig
import goannouncements
import crypto_db

from webapp2_extras import i18n
from webapp2_extras.i18n import gettext as _

class SlackOAuthComplete(webapp2.RequestHandler):

    def get(self):
        the_band_key = ndb.Key(urlsafe=self.request.get("bk"))
        the_band = the_band_key.get()

        if the_band is None:
            self.response.status = 400
            self.response.write('Error: did not find a band!')
            return

        secrets = crypto_db.get_cryptokey_object()

        oauth_info = slack_client.get_oauth_info(
            secrets.slack_client_id,
            secrets.slack_client_secret,
            self.request.get('code'),
            self.uri_for('slack_oauth_complete', _full=True, bk=the_band.key.urlsafe())
            )

        logging.info("Slack credentials successfully retrieved for {0}".format(the_band.name))
        the_band.slack_bot_user_id = oauth_info['bot']['bot_user_id']
        the_band.slack_bot_access_token = oauth_info['bot']['bot_access_token']
        the_band.put()


        return self.redirect(self.uri_for('edit_band', bk=self.request.get("bk")))

class SlackGigHandler(webapp2.RequestHandler):

    def post(self):
        the_shared_params = pickle.loads(self.request.get('the_shared_params'))
        the_gig = the_shared_params['the_gig_key'].get()
        the_band_key = the_shared_params['the_band_key']
        the_band = the_band_key.get()
        the_gig_url = self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe())
        the_channel = the_band.slack_announcements_channel or "#general"
        is_edit = the_shared_params['is_edit']
        is_reminder = the_shared_params['is_reminder']
        change_string = the_shared_params['change_string']

        # We need a member to localize the date string. Pick the first admin
        # for the band to determine localization. If no admin is found, pick
        # the first invited member.
        admins = assoc.get_admin_members_from_band_key(the_band_key)
        if len(admins) > 0:
            a_member = admins[0]
        else:
            # TODO: This will blow up if the band has no confirmed members
            a_member = assoc.get_confirmed_assocs_of_band_key(the_band_key)[0].member.get()

        logging.info("Found member {0} and gig date {1}".format(a_member, the_gig.date))

        if is_edit:
            title_string='{0} ({1})'.format(_('Gig Edit'), change_string)
        elif is_reminder:
            title_string=_("Gig Reminder")
        else:
            title_string=_("New Gig")

        the_date_string = goannouncements.format_date_string(the_gig.date, a_member)
        the_time_string = goannouncements.format_time_string(the_gig)
        the_status_string = [_('Unconfirmed'), _('Confirmed!'), _('Cancelled!')][the_gig.status]

        logging.info('announcing gig {0} to {1} Slack channel {2} '.format(
            the_gig.title,
            the_band.name,
            the_channel
            ))


        sc = SlackClient(the_band.slack_bot_access_token)
        sc.post_message(
            the_channel,
            "{}: \"{}\" ({})\n"
            "{} {}\n"
            "\n"
            "{}: {}".format(
                title_string,
                the_gig.title,
                the_status_string,
                the_date_string,
                the_time_string,
                _("Details"),
                the_gig_url
                ),
            False # as_user
            )

        self.response.write( 200 )
