from google.appengine.api import users

import webapp2
from member import *
from assoc import *
from gig import *

from jinja2env import jinja_environment as je
import debug
    
class MainPage(webapp2.RequestHandler):

    def get(self):    
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)
            
    def make_page(self,user):
        debug_print('IN AGENDA {0}'.format(user.nickname()))
        
        member=get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if member is None:
            return # todo figure out what to do if we get this far and there's no member
            
        # find the bands this member is associated with
        bands=get_bands_of_member(member)
        
        if bands is None:
            return # todo figure out what to do if there are no bands for this member
            
        if len(bands) > 1:
            return # todo figure out what to do if there is more than one band for this member
        
        band=bands[0]
        
        gigs=get_gigs_for_band(band)
        
        gig_info=[]
        for gig in gigs:
            gig_info.append( [gig.title, gig.key.id()] )
        
        template = je.get_template('agenda.html')
        self.response.write( template.render(
            title='Agenda',
            band=band,
            band_id=band.key.id(),
            gigs=gig_info,
            home_is_active=True
        ) )        
