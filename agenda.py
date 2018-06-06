from google.appengine.api import users

from requestmodel import *

import webapp2
import member
import gig
import plan
import band
import assoc
import logging
from colors import colors

from debug import debug_print
    
import datetime
from pytz.gae import pytz

class MainPage(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for agenda view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for agenda view """
        
        # find the bands this member is associated with
        the_assocs = assoc.get_confirmed_assocs_of_member(the_user, include_hidden=False)
        the_band_keys = [a.band for a in the_assocs]
        
        if the_band_keys is None or len(the_band_keys)==0:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))

        if the_user.show_long_agenda:
            num_to_put_in_upcoming=1000
        else:
            num_to_put_in_upcoming=5

        show_canceled=True
        if the_user.preferences and the_user.preferences.hide_canceled_gigs:
            show_canceled=False
            

        all_gigs = gig.get_sorted_gigs_from_band_keys(the_band_keys=the_band_keys, include_canceled=show_canceled)

        upcoming_plans = []
        weighin_plans = []        

        if all_gigs:
            for i in range(0, len(all_gigs)):
                a_gig = all_gigs[i]
                the_plan = plan.get_plan_for_member_for_gig(the_user, a_gig)

                info_block={}
                info_block['the_gig_key'] = a_gig.key
                info_block['the_plan_key'] = the_plan.key
                info_block['the_member_key'] = the_user.key
                a_band_key = a_gig.key.parent()
                a_band = None
                for test_band_key in the_band_keys:
                    if test_band_key == a_band_key:
                        a_band_key = test_band_key
                        break
                if a_band_key == None:
                    logging.error('agenda.MainPage error: no band for gig')
                    continue
                info_block['the_band'] = a_band_key.get()
                info_block['the_assoc'] = assoc.get_assoc_for_band_key_and_member_key(the_user.key, a_band_key)
                if the_plan.section is None:
                    if info_block['the_assoc']:
                        info_block['the_section'] = info_block['the_assoc'].default_section
                    else:
                        logging.error('agenda page: plan exists but no assoc: {0}'.format(the_plan.key.urlsafe()))
                        info_block['the_section'] = None

                else:
                    info_block['the_section'] = the_plan.section
                if num_to_put_in_upcoming and i<num_to_put_in_upcoming and (the_plan.value or a_gig.status == 2): #include gigs for which we've weighed in or have been cancelled
                    upcoming_plans.append( info_block )
                else:            
                    if (the_plan.value == 0 ):
                        weighin_plans.append( info_block )

        number_of_bands = len(the_band_keys)


        template_args = {
            'upcoming_plans' : upcoming_plans,
            'weighin_plans' : weighin_plans,
            'show_band' : number_of_bands>1,
            'long_agenda' : the_user.show_long_agenda,
            'the_date_formatter' : member.format_date_for_member,
            'agenda_is_active' : True,
            'colors' : colors
        }
        self.render_template('agenda.html', template_args)


class SwitchView(BaseHandler):
    @user_required
    def get(self):    
        """ get handler for agenda view """
        the_user=self.user
        
        if the_user.show_long_agenda:
            the_user.show_long_agenda=False
        else:
            the_user.show_long_agenda=True
        the_user.put()
        return self.redirect(self.uri_for("home"))