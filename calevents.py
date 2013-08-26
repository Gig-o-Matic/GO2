# get events for the calendar view!

from google.appengine.api import users

import webapp2
import json
import datetime
from band import *
from gig import *
    
class MainPage(webapp2.RequestHandler):

    def post(self):
    
        user = users.get_current_user()

        if not user:
            print 'CALEVENTS: NO USER' # todo figure out better way to handle
        else:
            args=self.request.arguments()
            
            start_date=datetime.date.fromtimestamp(int(self.request.get('start')))
            end_date=datetime.date.fromtimestamp(int(self.request.get('end')))
            band_id=int(self.request.get('band_id'))
            
            band=get_band_from_id(band_id)
            
            gigs=get_gigs_for_band_for_dates(band, start_date, end_date)
            
            events=[]
            for gig in gigs:
                events.append({\
                                'title':gig.title, \
                                'start':str(gig.date),  \
                                'url':'http:/gig_info.html?band_id={0}&gig_id={1}'.format(band_id,gig.key.id()) \
                                })
            
            testevent=json.dumps(events)
                        
            self.response.write( testevent )
