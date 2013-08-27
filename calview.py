from google.appengine.api import users

import webapp2
import member
import assoc
import gig
import datetime
import band
import json
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
        debug_print('IN CALVIEW {0}'.format(user.nickname()))
        
        the_member=member.get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if the_member is None:
            return # todo figure out what to do if we get this far and there's no member
            
        # find the bands this member is associated with
        bands=member.get_bands_of_member(the_member)
        
        if bands is None:
            return # todo figure out what to do if there are no bands for this member
            
        if len(bands) > 1:
            return # todo figure out what to do if there is more than one band for this member
        
        the_band=bands[0]
        
        gigs=gig.get_gigs_for_band(the_band)
        
        gig_info=[]
        for a_gig in gigs:
            gig_info.append( [a_gig.title, a_gig.key.id()] )
        
        template = je.get_template('calview.html')
        self.response.write( template.render(
            title='Calendar',
            member=member,
            logout_link=users.create_logout_url('/'),
            band=the_band,
            gigs=gig_info,
            calview_is_active=True
        ) )        

class CalEvents(webapp2.RequestHandler):

    def post(self):    
        user = users.get_current_user()

        if not user:
            print 'CALEVENTS: NO USER' # todo figure out better way to handle
        else:
            args=self.request.arguments()
            
            start_date=datetime.date.fromtimestamp(int(self.request.get('start')))
            end_date=datetime.date.fromtimestamp(int(self.request.get('end')))
            band_id=int(self.request.get('band_id'))
            
            the_band=band.get_band_from_id(band_id)
            
            gigs=gig.get_gigs_for_band_for_dates(the_band, start_date, end_date)
            
            events=[]
            for a_gig in gigs:
                events.append({\
                                'title':a_gig.title, \
                                'start':str(a_gig.date),  \
                                'url':'/gig_info.html?band_id={0}&gig_id={1}'.format(band_id,a_gig.key.id()) \
                                })
            
            testevent=json.dumps(events)
                        
            self.response.write( testevent )
