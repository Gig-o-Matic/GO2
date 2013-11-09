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
        """ get handler for agenda view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for agenda view """
        
        # find the bands this member is associated with
        the_assocs = assoc.get_confirmed_assocs_of_member(the_user)
        the_bands = [a.band.get() for a in the_assocs]
        
        if the_bands is None or len(the_bands)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))

        if the_user.show_long_agenda:
            num_to_put_in_upcoming=1000
        else:
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
                info_block['the_assoc'] = assoc.get_assoc_for_band_key_and_member_key(the_user.key, the_band_key)
                if the_plan.section is None:
                    info_block['the_section'] = info_block['the_assoc'].default_section
                else:
                    info_block['the_section'] = the_plan.section
                if num_to_put_in_upcoming and i<num_to_put_in_upcoming and the_plan.value:
                    upcoming_plans.append( info_block )
                else:            
                    if (the_plan.value == 0 ):
                        weighin_plans.append( info_block )

        number_of_bands = member.member_count_bands(the_user.key)


        template_args = {
            'title' : 'Schedule',
            'upcoming_plans' : upcoming_plans,
            'weighin_plans' : weighin_plans,
            'show_band' : number_of_bands>1,
            'long_agenda' : the_user.show_long_agenda,
            'agenda_is_active' : True
        }
        self.render_template('agenda.html', template_args)


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