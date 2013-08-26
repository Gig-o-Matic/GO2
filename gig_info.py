from google.appengine.api import users
import webapp2
from gig import *
from member import *
from band import *

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
        debug_print('IN GIG_INFO {0}'.format(user.nickname()))
        
        member=get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if member is None:
            return # todo figure out what to do if we get this far and there's no member

        # which band are we talking about?
        band_id=self.request.get("band_id",None)
        if band_id is None:
            self.response.write('no band id passed in!')
            return # todo figure out what to do if there's no ID passed in

        # find the gig we're interested in
        gig_id=self.request.get("gig_id", None)
        if gig_id is None:
            self.response.write('no gig id passed in!')
            return # todo figure out what to do if there's no ID passed in

        band=get_band_from_id(band_id) # todo more efficient if we include the band key?
        
        if band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it

            
        gig=get_gig_from_id(band, gig_id) # todo more efficient if we include the band key?
        
        if gig is None:
            self.response.write('did not find a gig!')
            return # todo figure out what to do if we didn't find it
            
        debug_print('found gig object: {0}'.format(gig.title))
                    
        template = je.get_template('gig_info.html')
        self.response.write( template.render(
            title='Gig Info',
            member=member,
            logout_link=users.create_logout_url('/'),            
            gig=gig,
            gig_id=gig.key.id(),
            band_id=band_id
        ) )        
