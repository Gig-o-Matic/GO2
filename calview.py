
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
import plan 

from debug import debug_print


class MainPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
                
        template_args = {
            'calview_is_active' : True
        }
        self.render_template('calview.html', template_args)


class CalEvents(BaseHandler):

    def post(self):    
        the_user = self.user
        
        start_date=datetime.datetime.strptime( self.request.get('start'), "%Y-%m-%d" )
        end_date=datetime.datetime.strptime( self.request.get('end'), "%Y-%m-%d" )+datetime.timedelta(days=1)

        the_member_keyurl=self.request.get('mk',0)
        
        if the_member_keyurl==0:
            return # todo figure out what to do
            
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_member = the_member_key.get()
        
        the_bands = assoc.get_confirmed_bands_of_member(the_member)

        gigs = []

        for a_band in the_bands:
            a_band_name = a_band.shortname if a_band.shortname else a_band.name
            all_gigs = gig.get_gigs_for_band_keys(a_band.key)
            for a_gig in all_gigs:
                if not a_gig.is_canceled and not a_gig.is_archived:
                    the_plan = plan.get_plan_for_member_key_for_gig_key(the_member_key, a_gig.key)
                    if the_plan:
                        # check member preferences
                        # include gig if member wants to see all, or if gig is confirmed
                        if a_gig.is_confirmed or the_member.preferences.calendar_show_only_confirmed == False:
                            # incude gig if member wants to see all, or if has registered as maybe or definitely:
                            if (the_plan.value > 0 and the_plan.value <= 3) or \
                                (the_member.preferences.calendar_show_only_committed == False):
                                    gigs.append(a_gig)
        
        events=[]
        colors=['#FF9F80','#D1F2A5','#EFFAB4','#FFC48C','#F56991']
        the_band_keys = [b.key for b in the_bands]
        num_bands = len(the_band_keys)
        
        for a_gig in gigs:
            band_key=a_gig.key.parent()

            cindex = the_band_keys.index(band_key) % len(colors)            

            the_title = a_gig.title
            if num_bands > 1:
                the_band = band_key.get()
                if the_band.shortname:
                    the_title = '{0}:\n{1}'.format(the_band.shortname, the_title)
                else:
                    the_title = '{0}:\n{1}'.format(the_band.name, the_title)
            

            events.append({
                            'title':the_title,
                            'start':str(a_gig.date.date()),
                            'end': str(a_gig.enddate+datetime.timedelta(days=1)) if a_gig.enddate else None,
                            'url':'/gig_info.html?gk={0}'.format(a_gig.key.urlsafe()),
                            'color':colors[cindex]
                            })
        
        testevent=json.dumps(events)
                    
        self.response.write( testevent )
