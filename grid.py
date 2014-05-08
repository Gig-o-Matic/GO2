from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import gig
import plan
import band
import assoc

from debug import debug_print
    
import datetime

class MainPage(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for grid view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for grid view """
        
        # find the bands this member is associated with
        if not the_user.is_superuser:
            the_assocs = assoc.get_confirmed_assocs_of_member(the_user)
            the_band_keys = [a.band for a in the_assocs]
        else:
            the_band_keys = band.get_all_bands(keys_only=True)
        
        if the_band_keys is None or len(the_band_keys)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))
            
        # find the band we're interested in
        band_key_str=self.request.get("bk", None)
        if band_key_str is None:
            the_band_key = the_band_keys[0]
        else:
            the_band_key = ndb.Key(urlsafe=band_key_str)

        month_str=self.request.get("m",None)
        year_str=self.request.get("y",None)
        if month_str==None or year_str==None:
            start_date = datetime.datetime.now().replace(day=1)
        else:
            delta=0
            delta_str=self.request.get("d",None)
            if delta_str != None:
                delta=int(delta_str)
            year=int(year_str)
            month=int(month_str)
            month=month+delta
            if month>12:
                month = 1
                year = year+1
            if month<1:
                month=12
                year = year-1
            start_date = datetime.datetime(year=year, month=month, day=1)
        
        end_date = start_date
        if (end_date.month < 12):
            end_date = end_date.replace(month = end_date.month + 1, day = 1)
        else:
            end_date = end_date.replace(year = end_date.year + 1, month=1, day=1)

        show_canceled=True
        if the_user.preferences and the_user.preferences.hide_canceled_gigs:
            show_canceled=False

        the_gigs = gig.get_gigs_for_band_key_for_dates(the_band_key, start_date, end_date, get_canceled=show_canceled)
        the_member_assocs = band.get_assocs_of_band_key_by_section_key(the_band_key, include_occasional=False)

        the_plans = {}
        for section in the_member_assocs:
            for assoc in section[1]:
                member_key=assoc.member
                member_plans = {}
                for a_gig in the_gigs:
                    the_plan = plan.get_plan_for_member_key_for_gig_key(the_member_key=member_key, the_gig_key=a_gig.key)
                    member_plans[a_gig.key] = the_plan.value
                the_plans[member_key] = member_plans
                

        template_args = {
            'all_band_keys' : the_band_keys,
            'the_band_key' : the_band_key,
            'the_member_assocs_by_section' : the_member_assocs,
            'the_month_string' : member.format_date_for_member(the_user, start_date, 'month'),
            'the_month' : start_date.month,
            'the_year' : start_date.year,
            'the_date_formatter' : member.format_date_for_member,
            'the_gigs' : the_gigs,
            'the_plans' : the_plans,
            'grid_is_active' : True
        }
        self.render_template('grid.html', template_args)
