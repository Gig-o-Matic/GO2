from google.appengine.api import users

from requestmodel import *
from restify import rest_user_required, CSOR_Jsonify

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


def _get_agenda_contents_for_member(the_user):
    # find the bands this member is associated with
    the_assocs = assoc.get_confirmed_assocs_of_member(the_user, include_hidden=False)
    the_band_keys = [a.band for a in the_assocs]

    if the_band_keys is None or len(the_band_keys)==0:
        raise Exception("no agenda")

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
            info_block['the_gig'] = a_gig
            info_block['the_plan'] = the_plan
            info_block['the_member'] = the_user
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
                    info_block['the_section_key'] = info_block['the_assoc'].default_section
                else:
                    logging.error('agenda page: plan exists but no assoc: {0}'.format(the_plan.key.urlsafe()))
                    info_block['the_section_key'] = None

            else:
                info_block['the_section_key'] = the_plan.section
            if num_to_put_in_upcoming and i<num_to_put_in_upcoming and (the_plan.value or a_gig.status == 2): #include gigs for which we've weighed in or have been cancelled
                upcoming_plans.append( info_block )
            else:            
                if (the_plan.value == 0 ):
                    weighin_plans.append( info_block )

    number_of_bands = len(the_band_keys)

    return (upcoming_plans, weighin_plans, number_of_bands)


class MainPage(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for agenda view """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for agenda view """
        
        try:
            (upcoming_plans, weighin_plans, number_of_bands) = _get_agenda_contents_for_member(the_user)
        except:
            return self.redirect('/member_info.html?mk={0}'.format(the_user.key.urlsafe()))

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


# For the REST agenda interface, just return list of gigs
def _RestGetInfo(info_block):
    info = {}
    info['gig'] = gig._RestGigInfo(info_block['the_gig'])
    info['plan'] = plan._RestPlanInfo(info_block['the_plan'])
    info['band'] = band._RestBandInfo(info_block['the_band'], include_id=False, name_only=True)

    return info

class RestEndpoint(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self):
        try:
            (upcoming_plans, weighin_plans, number_of_bands) = _get_agenda_contents_for_member(self.user)
        except:
            return {
                'upcoming_plans' : [],
                'weighin_plans' : [],
            }

        return {
            'upcoming_plans' : [_RestGetInfo(g) for g in upcoming_plans],
            'weighin_plans' : [_RestGetInfo(g) for g in weighin_plans],
        }



