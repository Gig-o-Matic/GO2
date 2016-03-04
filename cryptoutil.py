"""

 crypto utils for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 March 2016

"""

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models
import webapp2

import crypto_db
import member

class AdminPage(BaseHandler):
    """ Page for cryptokey administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):
    
        template_args = {
            'current' : crypto_db.get_cryptokey()
        }
        self.render_template('crypto_admin.html', template_args)


    @user_required
    def post(self):
        the_cryptokey=self.request.get('cryptokey_content','')
        crypto_db.set_cryptokey(the_cryptokey)
        self.redirect(self.uri_for('crypto_admin'))
