from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import gig
import plan
import band
import assoc

from jinja2env import jinja_environment as je
from debug import debug_print
    
import datetime

class MainPage(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for grid view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for grid view """
        
        # find the bands this member is associated with
        the_assocs = assoc.get_confirmed_assocs_of_member(the_user)
        the_band_keys = [a.band for a in the_assocs]
        
        if the_band_keys is None or len(the_band_keys)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))
            
        start_date = datetime.datetime.now()
        end_date = datetime.datetime.now()
        if (end_date.month < 12):
            end_date = end_date.replace(month = end_date.month + 1, day = 1)
        else:
            end_date = end_date.replace(year = end_date.year + 1, month=1, day=1)
        
        the_band_key = the_band_keys[0]
        the_gigs = gig.get_gigs_for_band_key_for_dates(the_band_key, start_date, end_date)
        the_member_keys = band.get_member_keys_of_band_key_by_section_key(the_band_key)

        the_plans = {}
        for section in the_member_keys:
            for member_key in section[1]:
                member_plans = {}
                for a_gig in the_gigs:
                    the_plan = plan.get_plan_for_member_key_for_gig_key(the_member_key=member_key, the_gig_key=a_gig.key)
                    member_plans[a_gig.key] = the_plan.value
                the_plans[member_key] = member_plans
                

        template_args = {
            'title' : "Grid o'Gigs",
            'the_band_key' : the_band_key,
            'the_member_keys_by_section' : the_member_keys,
            'the_month' : start_date.strftime("%B, %Y"),
            'the_gigs' : the_gigs,
            'the_plans' : the_plans
        }
        self.render_template('grid.html', template_args)


class SwitchView(BaseHandler):
    @user_required
    def get(self):    
        """ get handler for agenda view """
        the_user=self.user
        
        if the_user.show_long_agenda:
            the_user.show_long_agenda=False
        else:
            the_user.show_long_agenda=True
        the_user.put()
        return self.redirect(self.uri_for("home"))