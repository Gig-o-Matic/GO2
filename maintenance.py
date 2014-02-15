"""

 maintenance mode class for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 December 2013

"""

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2


class MaintenancePage(BaseHandler):
    """ class to serve the maintenance info page """

    def get(self):    
        self._make_page()

    def _make_page(self):

        template_args = {}
        self.render_nouser_template('maintenance.html', template_args)
        return