
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

        print '\n\n'
        print self.request.get('start')
        print '\n\n'
        
#         start_date=datetime.datetime.fromtimestamp(int(self.request.get('start')))
#         end_date=datetime.datetime.fromtimestamp(int(self.request.get('end')))

        start_date=datetime.datetime.strptime( self.request.get('start'), "%Y-%m-%d" )
        end_date=datetime.datetime.strptime( self.request.get('end'), "%Y-%m-%d" )+datetime.timedelta(days=1)

        the_member_key=self.request.get('mk',0)
        
        if the_member_key==0:
            return # todo figure out what to do
            
        the_member=ndb.Key(urlsafe=the_member_key).get()
        
        
        the_bands = assoc.get_band_keys_of_member_key(the_member.key, confirmed_only=True)
        num_bands = len(the_bands)
        
        gigs=gig.get_gigs_for_member_for_dates(the_member=the_member, start_date=start_date, end_date=end_date, get_canceled=False)
        
        events=[]
        colors=['#FF9F80','#D1F2A5','#EFFAB4','#FFC48C','#F56991']

        for a_gig in gigs:
            band_key=a_gig.key.parent()

            cindex = the_bands.index(band_key) % len(colors)            

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
                            'end': str(a_gig.enddate+datetime.timedelta(days=1)) if a_gig.enddate else None,
                            'url':'/gig_info.html?gk={0}'.format(a_gig.key.urlsafe()),
                            'color':colors[cindex]
                            })
        
        testevent=json.dumps(events)
                    
        self.response.write( testevent )
