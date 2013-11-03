
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
import member
import gig
import datetime
import band
import json
import assoc

from debug import debug_print


class MainPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
                
        template_args = {
            'title' : 'Calendar',
            'calview_is_active' : True,
        }
        self.render_template('calview.html', template_args)


class CalEvents(BaseHandler):

    def post(self):    
        the_user = self.user
        
        start_date=datetime.datetime.fromtimestamp(int(self.request.get('start')))
        end_date=datetime.datetime.fromtimestamp(int(self.request.get('end')))
        the_member_key=self.request.get('mk',0)
        
        if the_member_key==0:
            return # todo figure out what to do
            
        the_member=ndb.Key(urlsafe=the_member_key).get()
        
        num_bands = len(assoc.get_band_keys_of_member_key(the_member.key, confirmed_only=True))
        
        gigs=gig.get_gigs_for_member_for_dates(the_member, start_date, end_date)
        
        events=[]
        colors=['#FF88FF','#55c0c0','#d0d0d0','#f0f055','#77f077','#ff8888']
        cindex=0
        taken_colors={}
        for a_gig in gigs:
            band_key=a_gig.key.parent()
            if band_key in taken_colors:
                now_color=taken_colors[band_key]
            else:
                if cindex >= len(colors):
                    cindex=0
                now_color=colors[cindex]
                cindex=cindex+1
                taken_colors[band_key]=now_color

            the_title = a_gig.title
            if num_bands > 1:
                the_band = band_key.get()
                if the_band.shortname:
                    the_title = '{0}:\n{1}'.format(the_band.shortname, the_title)
                else:
                    the_title = '{0}:\n{1}'.format(the_band.name, the_title)
            

            events.append({
                            'title':the_title,
                            'start':str(a_gig.date),
                            'url':'/gig_info.html?gk={0}'.format(a_gig.key.urlsafe()),
                            'color':now_color
                            })
        
        testevent=json.dumps(events)
                    
        self.response.write( testevent )
