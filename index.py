from google.appengine.api import users

import webapp2
from jinja2env import jinja_environment as je

class MainPage(webapp2.RequestHandler):

    def get(self):
    
        user = users.get_current_user()

        if user:
            make_test.test_band()       
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
