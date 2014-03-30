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
import datetime

def make_cal_header(the_band):
    header="""BEGIN:VCALENDAR
PRODID:-//Gig-o-Matic//Gig-o-Matic 2//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{0}
X-WR-CALDESC:{2}
"""

# X-WR-TIMEZONE:{1}

    return header.format(the_band.name,'',"Gig-o-Matic calendar for {0}".format(the_band.name))

def make_cal_footer():
    return "END:VCALENDAR\n"

def make_event(the_gig, the_band):
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

    dtstart = the_gig.date.strftime("%Y%m%d")

    if the_gig.enddate:
        dtend = the_gig.enddate.strftime("%Y%m%d")
    else:
        dtend = the_gig.date.strftime("%Y%m%d")
    
    starthour = -1
    endhour = -1
    
    if the_gig.calltime:
        ct = None
        try:
            ct = datetime.datetime.strptime(the_gig.calltime,"%I:%M%p")
        except:
            try:
                ct = datetime.datetime.strptime(the_gig.calltime,"%H:%M")
            except:
                pass # TODO convert to real time objects; for now punt

        if ct:
            starthour = ct.hour
            startmin = ct.minute

    elif the_gig.settime: # only use the set time if there's no call time
        st = None
        try:
            st = datetime.datetime.strptime(the_gig.settime,"%I:%M%p")
        except:
            try:
                st = datetime.datetime.strptime(the_gig.settime,"%H:%M")
            except: 
                pass # TODO convert to real time objects; for now punt

        if st:
            starthour = st.hour
            startmin = st.minute

    et = None
    if the_gig.endtime:
        try:
            et = datetime.datetime.strptime(the_gig.endtime,"%I:%M%p")
        except:
            try:
                et = datetime.datetime.strptime(the_gig.endtime,"%H:%M")
            except:
                pass

    if et:
        endhour = et.hour
        endmin = et.minute
    elif starthour >= 0:
            endhour = starthour + 1
            endmin = startmin


    if starthour >= 0:
        starthour = starthour - the_band.time_zone_correction
        dtstart = '{0}T{1:02d}{2:02d}00Z'.format(dtstart,starthour,startmin)
    if endhour >= 0:
        endhour = endhour - the_band.time_zone_correction
        dtend = '{0}T{1:02d}{2:02d}00Z'.format(dtend,endhour,endmin)

    the_url = 'http://gig-o-matic.appspot.com/gig_info.html?gk={0}'.format(the_gig.key.urlsafe())

    event="""BEGIN:VEVENT
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
    event=event.format(summary, dtstart, dtend, the_gig.details, the_gig.address, the_url)
    return event

#####
#
# Page Handlers
#
#####

class RequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):
        print 'got get request'

        bk = kwargs['bk']
            
        the_band_key = ndb.Key(urlsafe=bk);
        the_band = the_band_key.get()

        info = '{0}'.format(make_cal_header(the_band))

        all_gigs = gig.get_gigs_for_band_keys(the_band_key)
        for a_gig in all_gigs:
            if a_gig.is_confirmed:
                info = '{0}{1}'.format(info, make_event(a_gig, the_band))

        info = '{0}{1}'.format(info, make_cal_footer())
        self.response.write(info)
            
    def post(self):    
        print 'got post request'
            
