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
                    
        template = je.get_template('member_info.html')
        self.response.write( template.render(
            title='Member Info',
            member=member,
            bands=bands
        ) )        
