#
#  caldav server class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 29 March 2014
#
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
import logging

import gig
import assoc
import band
import plan

import datetime
from pytz.gae import pytz

def make_cal_header(the_title):
    header="""BEGIN:VCALENDAR
PRODID:-//Gig-o-Matic//Gig-o-Matic 2//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{0}
X-WR-CALDESC:{1}
"""

# X-WR-TIMEZONE:{1}

    return header.format(the_title,"Gig-o-Matic calendar for {0}".format(the_title))

def make_cal_footer():
    return "END:VCALENDAR\n"

def make_event(the_gig, the_band, title_format=u'{0}', details_format=u'{0}'):
# 
#     event="""BEGIN:VEVENT
# DTSTART:{1}
# DTEND:{2}
# DTSTAMP:20140329T155645Z
# UID:3jba27qkcfjmf9elvfs909fgdk@google.com
# CREATED:20140329T154445Z
# DESCRIPTION:
# LAST-MODIFIED:20140329T154445Z
# LOCATION:
# SEQUENCE:0
# STATUS:CONFIRMED
# SUMMARY:{0}
# TRANSP:OPAQUE
# END:VEVENT
# """

    summary = the_gig.title

    # make real gig start time, assuming everything is in local time
    start_dt = the_gig.date
    if the_gig.enddate:
        end_dt = the_gig.enddate
    else:
        end_dt = start_dt
    
    starttime_dt = None
    endtime_dt = None
    if the_gig.calltime:
        try:
            starttime_dt = datetime.datetime.strptime(the_gig.calltime,"%I:%M%p")
        except:
            try:
                starttime_dt = datetime.datetime.strptime(the_gig.calltime,"%H:%M")
            except:
                pass # TODO convert to real time objects; for now punt

    if starttime_dt is None and the_gig.settime: # only use the set time if there's no call time
        try:
            starttime_dt = datetime.datetime.strptime(the_gig.settime,"%I:%M%p")
        except:
            try:
                starttime_dt = datetime.datetime.strptime(the_gig.settime,"%H:%M")
            except: 
                pass # TODO convert to real time objects; for now punt

    if the_gig.endtime:
        try:
            endtime_dt = datetime.datetime.strptime(the_gig.endtime,"%I:%M%p")
        except:
            try:
                endtime_dt = datetime.datetime.strptime(the_gig.endtime,"%H:%M")
            except:
                pass # TODO convert to real time objects; for now punt


    if starttime_dt and endtime_dt is None:
        # no end time - use the start time if there is one, plus 1 hour
        if starttime_dt:
            endtime_dt = starttime_dt + datetime.timedelta(hours=1)

    if starttime_dt:
        start_dt = datetime.datetime.combine(start_dt, starttime_dt.time())
    
    if endtime_dt and end_dt:
        end_dt = datetime.datetime.combine(end_dt, endtime_dt.time())


    if end_dt < start_dt:
        end_dt = end_dt+ datetime.timedelta(days=1)

    # do the setup so we can do timezone math
    if the_band.timezone:
        start_dt = start_dt.replace(tzinfo = pytz.timezone(the_band.timezone))
        end_dt = end_dt.replace(tzinfo = pytz.timezone(the_band.timezone))
        if starttime_dt:
            tzcorr = datetime.datetime.now(pytz.timezone(the_band.timezone)).dst()
        else:
            tzcorr = datetime.timedelta(0)
        start_dt = start_dt.astimezone(pytz.utc) - tzcorr
        end_dt = end_dt.astimezone(pytz.utc) - tzcorr
    else:
        start_dt = start_dt.replace(tzinfo = pytz.utc)
        end_dt = end_dt.replace(tzinfo = pytz.utc)
            
    start_string = start_dt.strftime('%Y%m%d')
    end_string = end_dt.strftime('%Y%m%d')
    
    # now, if we have a start time, append it
    if starttime_dt:
        start_string = '{0}T{1}'.format(start_string,start_dt.astimezone(pytz.utc).strftime("%H%M00Z"))

    if endtime_dt:
        end_string = '{0}T{1}'.format(end_string,end_dt.astimezone(pytz.utc).strftime("%H%M00Z"))
    
    the_url = 'http://gig-o-matic.appspot.com/gig_info.html?gk={0}'.format(the_gig.key.urlsafe())

    event=u"""BEGIN:VEVENT
DTSTART:{1}
DTEND:{2}
DESCRIPTION:{3}
LOCATION: {4}
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:{0}
TRANSP:OPAQUE
URL:{5}
END:VEVENT
"""
    event=event.format(title_format.format(summary), start_string, end_string, details_format.format(the_gig.details.replace('\r\n',' ')), the_gig.address, the_url)
    return event

#####
#
# Page Handlers
#
#####

class BandRequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):

        bk = kwargs['bk']
            
        the_band_key = ndb.Key(urlsafe=bk);
        the_band = the_band_key.get()

        info = u'{0}'.format(make_cal_header(the_band.name))

        all_gigs = gig.get_gigs_for_band_keys(the_band_key)
        for a_gig in all_gigs:
            if a_gig.is_confirmed:
                info = u'{0}{1}'.format(info, make_event(a_gig, the_band))

        info = u'{0}{1}'.format(info, make_cal_footer())
        self.response.write(info)
            
    def post(self):    
        print 'got post request'


class MemberRequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):

        mk = kwargs['mk']
            
        the_member_key = ndb.Key(urlsafe=mk)
        the_member = the_member_key.get()
        
        info = u'{0}'.format(make_cal_header(the_member.name))

        the_bands = assoc.get_confirmed_bands_of_member(the_member)

        for a_band in the_bands:
            a_band_name = a_band.shortname if a_band.shortname else a_band.name
            all_gigs = gig.get_gigs_for_band_keys(a_band.key, show_past=True)
            for a_gig in all_gigs:
                if not a_gig.is_canceled: # and not a_gig.is_archived:
                    the_plan = plan.get_plan_for_member_key_for_gig_key(the_member_key, a_gig.key)
                    if the_plan:
                        # check member preferences
                        # include gig if member wants to see all, or if gig is confirmed
                        if a_gig.is_confirmed or the_member.preferences.calendar_show_only_confirmed == False:
                            # incude gig if member wants to see all, or if has registered as maybe or definitely:
                            if (the_plan.value > 0 and the_plan.value <= 3) or \
                                (the_member.preferences.calendar_show_only_committed == False):
                                    if a_gig.is_confirmed:
                                        confstr=u'CONFIRMED!'
                                    else:
                                        confstr=u'(not confirmed)'
                                    info = u'{0}{1}'.format(info, make_event(a_gig, 
                                                                            a_band,
                                                                            title_format=u'{0}:{{0}} {1}'.format(a_band_name, confstr)))

        info = u'{0}{1}'.format(info, make_cal_footer())
        self.response.write(info)
            
    def post(self):    
        print 'got post request'
            

class HelpHandler(BaseHandler):
    """Handle a request for help"""

    @user_required
    def get(self):    
        """ get handler for help page """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for help """

        template_args = {
            'member' : the_user
        }
        self.render_template('calhelp.html', template_args)


