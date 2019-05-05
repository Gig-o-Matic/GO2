"""

 maintenance mode class for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 December 2013

"""

from requestmodel import *

class MaintenancePage(BaseHandler):
    """ class to serve the maintenance info page """

    def get(self):    
        self._make_page()

    def _make_page(self):

        template_args = {}
        self.render_nouser_template('maintenance.html', template_args)
        return