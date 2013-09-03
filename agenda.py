from google.appengine.api import users

import webapp2
import member
import assoc
import gig
import plan
import band

from jinja2env import jinja_environment as je
from debug import debug_print
    
class MainPage(webapp2.RequestHandler):

    def get(self):    
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)
            
    def make_page(self,user):
        debug_print('IN AGENDA {0}'.format(user.nickname()))
        
        the_user=member.get_member_from_nickname(user.nickname())
        
        
        
        # find the bands this member is associated with
        the_bands=member.get_bands_of_member(the_user)
        
        if the_bands is None:
            return # todo figure out what to do if there are no bands for this member
                    
        num_to_put_in_upcoming=2
        the_gigs=gig.get_gigs_for_band(the_bands, num=num_to_put_in_upcoming)
        
        upcoming_plans=[]
        weighin_plans=[]        
        all_gigs=gig.get_gigs_for_band(the_bands)
        for i in range(0, len(all_gigs)):
            a_gig=all_gigs[i]
            the_plan=plan.get_plan_for_member_for_gig(the_user, a_gig)
            if (i<num_to_put_in_upcoming):
                upcoming_plans.append( the_plan )
            else:            
                if (the_plan.value==0 ):
                    weighin_plans.append( the_plan )

        print 'sending in {0} upcoming and {1} weighins'.format(len(upcoming_plans),len(weighin_plans))

        template = je.get_template('agenda.html')
        self.response.write( template.render(
            title='Agenda',
            the_user=the_user,
            logout_link=users.create_logout_url('/'),
            upcoming_plans=upcoming_plans,
            weighin_plans=weighin_plans,
            nav_info=member.nav_info(the_user, None),          
            agenda_is_active=True
        ) )        
