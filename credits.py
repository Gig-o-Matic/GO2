from google.appengine.api import users

from requestmodel import *

import webapp2
    
class CreditsHandler(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for credits page """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for help """

        template_args = {}
        self.render_template('credits.html', template_args)
