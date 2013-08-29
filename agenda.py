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
        
        the_member=member.get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if the_member is None:
            return # todo figure out what to do if we get this far and there's no member
            
        # find the bands this member is associated with
        the_bands=member.get_bands_of_member(the_member)
        
        if the_bands is None:
            return # todo figure out what to do if there are no bands for this member
            
        if len(the_bands) > 1:
            return # todo figure out what to do if there is more than one band for this member
        
        the_band=the_bands[0]
        
        the_gigs=gig.get_gigs_for_band(the_band, num=2)
        
        gig_info=[]
        for a_gig in the_gigs:
            the_plan=plan.get_plan_for_member_for_gig(the_member, a_gig)
            gig_info.append( [a_gig, the_plan] )
        
        all_gigs=gig.get_gigs_for_band(the_band)
        weigh_ins=[]
        for a_gig in all_gigs:
            the_plan=plan.get_plan_for_member_for_gig(the_member, a_gig)
            if the_plan is None:
                weigh_ins.append( a_gig )

        template = je.get_template('agenda.html')
        self.response.write( template.render(
            title='Agenda',
            member=the_member,
            logout_link=users.create_logout_url('/'),
            band=the_band,
            band_id=the_band.key.id(),
            gigs=gig_info,
            weigh_ins=weigh_ins,
            agenda_is_active=True
        ) )        

class AgendaEvents(webapp2.RequestHandler):
    def post(self):
            print 'IN AGENDA EVENTS'
            
            band_id=int(self.request.get('band_id'))
            member_id=int(self.request.get('member_id'))
            maxnum=int(self.request.get('maxnum',0))
            if maxnum==0:
                maxnum=None
            noplan=int(self.request.get('noplan',0))
            
            the_band=band.get_band_from_id(band_id)
            the_gigs=gig.get_gigs_for_band(the_band, num=maxnum)
            the_member=member.get_member_from_id(member_id)
            
            gig_info=[]
            for a_gig in the_gigs:
                the_plan=plan.get_plan_for_member_for_gig(the_member, a_gig)
                if noplan != 0:
                    # we want gigs without a plan
                    if the_plan.value==0:
                        gig_info.append( [a_gig, the_plan] )
                else:
                    if the_plan is None:
                        gig_info.append( [a_gig, the_plan] )
                    else:
                        gig_info.append( [a_gig, the_plan.value] )

            template = je.get_template('agenda_events.html')
            self.response.write( template.render(
                gigs=gig_info,
                band_id=band_id
            ) )        
