
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
import member
import assoc
import gig
import datetime
import band
import json

from debug import debug_print


class MainPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
                
        template_args = {
            'title' : 'Calendar',
            'calview_is_active' : True,
            'nav_info' : member.nav_info(the_user, None)
        }
        self.render_template('calview.html', template_args)


class CalEvents(BaseHandler):

    def post(self):    
        the_user = self.user
        
        start_date=datetime.date.fromtimestamp(int(self.request.get('start')))
        end_date=datetime.date.fromtimestamp(int(self.request.get('end')))
        the_member_key=self.request.get('mk',0)
        
        if the_member_key==0:
            return # todo figure out what to do
            
        the_member=ndb.Key(urlsafe=the_member_key).get()
        
        gigs=gig.get_gigs_for_member_for_dates(the_member, start_date, end_date)
        
        events=[]
        for a_gig in gigs:
            events.append({\
                            'title':a_gig.title, \
                            'start':str(a_gig.date),  \
                            'url':'/gig_info.html?gk={0}'.format(a_gig.key.urlsafe()) \
                            })
        
        testevent=json.dumps(events)
                    
        self.response.write( testevent )
