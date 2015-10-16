#
#
#   Activity page: show recent changes to member plans for gigs
#
from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import gig
import plan
import band
import assoc
import logging

from debug import debug_print

import datetime

class MainPage(BaseHandler):

    @user_required
    def get(self):
        """ get handler for agenda view """
        self._make_page(the_user=self.user)

    def _make_page(self, the_user):
        """ construct page for activity view """


        the_band_key_urlsafe = self.request.get("bk", '0')
        if the_band_key_urlsafe == '0':
            return
        else:
            the_band_key = ndb.Key(urlsafe=the_band_key_urlsafe)
            if the_band_key is None:
                self.response.write('did not find a band!')
                return # todo figure out what to do if we didn't find it

        # get all of the plans related to this band key that changed in the last day
        the_changed_plans = plan.get_recent_changes_for_band_key(
            the_band_key=the_band_key, the_time_delta_days=1, keys_only=False)

        # sort the plans by gig
        change_gigs = {}
        for a_plan in the_changed_plans:
            the_change_gig = a_plan.key.parent()
            if the_change_gig in change_gigs:
                change_gigs[the_change_gig] = change_gigs[the_change_gig].append(a_plan)
            else:
                change_gigs[the_change_gig] = [a_plan]

        print "\nactivity:"
        print '{0}'.format(change_gigs)
        print "\n"

        template_args = {
            'the_band' : the_band_key.get(),
            'change_gigs' : change_gigs
        }
        self.render_template('band_activity.html', template_args)
