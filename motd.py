"""

 motd class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models
import webapp2

import motd_db
import member

class AdminPage(BaseHandler):
    """ Page for motd administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):
    
        template_args = {
            'current' : motd_db.get_motd()
        }
        self.render_template('motd_admin.html', template_args)


    @user_required
    def post(self):
        the_motd=self.request.get('motd_content','')
        motd_db.set_motd(the_motd)
        member.reset_motd()
        self.redirect(self.uri_for('home'))


class SeenHandler(BaseHandler):
    @user_required
    def post(self):    
        """ get handler for help page """

        the_member_keystr=self.request.get("mk",'0')
        
        if the_member_keystr=='0':
            return # todo what to do if it's not passed in?

        the_member_key = ndb.Key(urlsafe=the_member_keystr)       
        if the_member_key:
            member.set_seen_motd_for_member_key(the_member_key)
        else:
            return # todo what to do?

class SeenWelcomeHandler(BaseHandler):
    @user_required
    def post(self):    
        """ post handler for welcome page """

        the_member_keystr=self.request.get("mk",'0')
        
        if the_member_keystr=='0':
            return # todo what to do if it's not passed in?

        the_member_key = ndb.Key(urlsafe=the_member_keystr)       
        if the_member_key:
            member.set_seen_welcome_for_member_key(the_member_key)
        else:
            return # todo what to do?


