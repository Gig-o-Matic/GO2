from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import gig
import plan
import band

from jinja2env import jinja_environment as je
from debug import debug_print
    
import datetime

class MainPage(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for agenda view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for agenda view """
        

# {% set the_gig_key = plan_info['gig_key'] %}
# {% set the_plan_key = plan_info['plan_key'] %}
# {% set the_member_key = plan_info['member_key'] %}
# {% set the_band_key = plan_info['band_key'] %}
# {% set the_assoc = plan_info['assoc'] %}


        # find the bands this member is associated with
        the_assocs = member.get_confirmed_assocs_of_member(the_user)
        the_bands = [a.band.get() for a in the_assocs]
        
        if the_bands is None or len(the_bands)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))

        num_to_put_in_upcoming=5
        today_date = datetime.datetime.now()
        the_gigs = gig.get_gigs_for_bands(the_bands, num=num_to_put_in_upcoming, start_date=today_date)
        all_gigs = gig.get_gigs_for_bands(the_bands, start_date=today_date)

        upcoming_plans = []
        weighin_plans = []        

        if all_gigs:
            for i in range(0, len(all_gigs)):
                a_gig = all_gigs[i]
                the_plan = plan.get_plan_for_member_for_gig(the_user, a_gig)

                info_block={}
                info_block['the_gig_key'] = a_gig.key
                info_block['the_plan_key'] = the_plan.key
                info_block['the_member_key'] = the_user.key
                the_band_key = the_plan.key.parent().get().key.parent()
                info_block['the_band_key'] = the_band_key
                info_block['the_assoc'] = member.get_assoc_for_band_key(the_user, the_band_key)
                if (i<num_to_put_in_upcoming):
                    upcoming_plans.append( info_block )
                else:            
                    if (the_plan.value == 0 ):
                        weighin_plans.append( info_block )

        template_args = {
            'title' : 'Agenda',
            'upcoming_plans' : upcoming_plans,
            'weighin_plans' : weighin_plans,
            'agenda_is_active' : True
        }
        self.render_template('agenda.html', template_args)
