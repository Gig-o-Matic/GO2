from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import assoc
import gig
import plan
import band

from jinja2env import jinja_environment as je
from debug import debug_print
    
import datetime

class MainPage(BaseHandler):

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        debug_print('IN AGENDA {0}'.format(the_user.name))
        
        # find the bands this member is associated with
        the_bands=member.get_bands_of_member(the_user)
        
        if the_bands is None or len(the_bands)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))
                    
        num_to_put_in_upcoming=2
        today_date=datetime.datetime.now()
        print 'using start date {0}'.format(today_date)
        the_gigs=gig.get_gigs_for_band(the_bands, num=num_to_put_in_upcoming, start_date=today_date)
         
        upcoming_plans=[]
        weighin_plans=[]        
        all_gigs=gig.get_gigs_for_band(the_bands, start_date=today_date)
        if all_gigs:
            for i in range(0, len(all_gigs)):
                a_gig=all_gigs[i]
                the_plan=plan.get_plan_for_member_for_gig(the_user, a_gig)
                if (i<num_to_put_in_upcoming):
                    upcoming_plans.append( the_plan )
                else:            
                    if (the_plan.value==0 ):
                        weighin_plans.append( the_plan )

        print 'sending in {0} upcoming and {1} weighins'.format(len(upcoming_plans),len(weighin_plans))

        template_args = {
            'title' : 'Agenda',
            'upcoming_plans' : upcoming_plans,
            'weighin_plans' : weighin_plans,
            'nav_info' : member.nav_info(the_user, None),          
            'agenda_is_active' : True
        }
        self.render_template('agenda.html', template_args)
