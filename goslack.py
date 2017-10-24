import webapp2
from google.appengine.ext import ndb

import logging
import os

import slack_client

class SlackOAuthComplete(webapp2.RequestHandler):

    def get(self):
        the_band_key = ndb.Key(urlsafe=self.request.get("bk"))
        the_band = the_band_key.get()

        if the_band is None:
            self.response.status = 400
            self.response.write('Error: did not find a band!')
            return

        oauth_info = slack_client.get_oauth_info(
            os.environ["SLACK_CLIENT_ID"],
            os.environ["SLACK_CLIENT_SECRET"],
            self.request.get('code'),
            self.uri_for('slack_oauth_complete', _full=True, bk=the_band.key.urlsafe())
            )

        logging.info("Slack credentials successfully retrieved for {0}".format(the_band.name))
        the_band.slack_bot_user_id = oauth_info['bot']['bot_user_id']
        the_band.slack_bot_access_token = oauth_info['bot']['bot_access_token']
        the_band.put()


        return self.redirect(self.uri_for('edit_band', bk=self.request.get("bk")))
