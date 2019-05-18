
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
from colors import colors

from debug import debug_print


class MainPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        
        m = self.request.get('m',None)
        y = self.request.get('y',None)

        template_args = {
            'calview_is_active' : True
        }

        if m and y:
            template_args['m'] = m
            template_args['y'] = y
            
        self.render_template('calview.html', template_args)


class CalEvents(BaseHandler):

    def post(self):    
        the_user = self.user
        
        start_date=datetime.datetime.strptime( self.request.get('start'), "%Y-%m-%d" )
        end_date=datetime.datetime.strptime( self.request.get('end'), "%Y-%m-%d" )+datetime.timedelta(days=1)

        the_member_keyurl=self.request.get('mk',0)
        
        if the_member_keyurl==0:
            return # todo figure out what to do
            
        the_member = member.member_from_urlsafe(the_member_keyurl)

        the_assocs = assoc.get_confirmed_assocs_of_member_key(the_member.key)
        the_band_keys = [a.band for a in the_assocs]

        cindices={}
        for a in the_assocs:
            cindices[a.band] = a.color

        gigs = []

        all_gigs = gig.get_gigs_for_band_keys(the_band_keys, show_past=True, start_date=start_date, end_date=end_date)
        for a_gig in all_gigs:
            if not a_gig.is_canceled and not a_gig.hide_from_calendar:
                the_plan = plan.get_plan_for_member_key_for_gig_key(the_member.key, a_gig.key)
                if the_plan:
                    # check member preferences
                    # include gig if member wants to see all, or if gig is confirmed
                    if a_gig.is_confirmed or the_member.preferences.calendar_show_only_confirmed == False:
                        # incude gig if member wants to see all, or if has registered as maybe or definitely:
                        if (the_plan.value > 0 and the_plan.value <= 3) or \
                            (the_member.preferences.calendar_show_only_committed == False):
                                gigs.append(a_gig)
        
        events=[]
        num_bands = len(the_band_keys)
        band_names={}
        
        for a_gig in gigs:
            band_key=a_gig.key.parent()

#            cindex = the_band_keys.index(band_key) % len(colors)
            cindex = cindices[band_key]

            the_title = a_gig.title
            if num_bands > 1:
                if band_key in band_names.keys():
                    the_band_name = band_names[band_key]
                else:
                    the_band = band_key.get()
                    if the_band.shortname:
                        the_band_name = the_band.shortname
                    else:
                        the_band_name = the_band.name
                    band_names[band_key] = the_band_name

                the_title = u'{0}:\n{1}'.format(the_band_name, the_title)
            

            options= {
                'title':the_title,
                'start':str(a_gig.date.date()),
                'end': str(a_gig.enddate+datetime.timedelta(days=1)) if a_gig.enddate else None,
                'url':'/gig_info.html?gk={0}'.format(a_gig.key.urlsafe()),
                'color':colors[cindex],
            }
            if cindex == 0:
                options['textColor'] = '#000000'
                options['borderColor'] = '#aaaaaa'
            events.append(options)
        
        testevent=json.dumps(events)
                    
        self.response.write( testevent )
