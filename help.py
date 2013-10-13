from google.appengine.api import users

from requestmodel import *

import webapp2
from jinja2env import jinja_environment as je
    
class HelpHandler(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for help page """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for help """

        template_args = {
            'title' : 'Help',
            'help_is_active' : True
        }
        self.render_template('help.html', template_args)
