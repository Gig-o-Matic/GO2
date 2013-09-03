from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import member
import assoc
import gig
import datetime
import band
import json
from jinja2env import jinja_environment as je
from debug import debug_print


class MainPage(webapp2.RequestHandler):

    def get(self):    
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)
            
    def make_page(self,user):
        debug_print('IN CALVIEW {0}'.format(user.nickname()))
        
        the_member=member.get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if the_member is None:
            return # todo figure out what to do if we get this far and there's no member
                    
        template = je.get_template('calview.html')
        self.response.write( template.render(
            title='Calendar',
            the_user=the_member,
            calview_is_active=True,
            nav_info=member.nav_info(the_member, None)
        ) )        

class CalEvents(webapp2.RequestHandler):

    def post(self):    
        user = users.get_current_user()

        if not user:
            print 'CALEVENTS: NO USER' # todo figure out better way to handle
        else:
            args=self.request.arguments()
            
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
