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

class SeenHandler(BaseHandler):
    @user_required
    def post(self):    
        """ get handler for help page """

        print 'setting motd seen'

        the_member_keystr=self.request.get("mk",'0')
        
        if the_member_keystr=='0':
            return # todo what to do if it's not passed in?

        the_member_key = ndb.Key(urlsafe=the_member_keystr)       
        if the_member_key:
            member.set_seen_motd_for_member_key(the_member_key)
        else:
            return # todo what to do?


