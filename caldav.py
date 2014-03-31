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
from pytz.gae import pytz

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
    elif the_gig.settime: # only use the set time if there's no call time
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

    else:
        endtime_dt = starttime_dt + datetime.timedelta(hours=1)

    if starttime_dt:
        start_dt = datetime.datetime.combine(start_dt, starttime_dt.time())
    
    if endtime_dt and end_dt:
        end_dt = datetime.datetime.combine(end_dt, endtime_dt.time())


    # do the setup so we can do timezone math
    if the_band.timezone:
        start_dt = start_dt.replace(tzinfo = pytz.timezone(the_band.timezone))
        end_dt = end_dt.replace(tzinfo = pytz.timezone(the_band.timezone))
    else:
        start_dt = start_dt.replace(tzinfo = pytz.utc)
        end_dt = end_dt.replace(tzinfo = pytz.utc)

    # finally, deal with daylight savings time
    if the_band.timezone:
        tzcorr = datetime.datetime.now(pytz.timezone(the_band.timezone)).dst()
    else:
        tzcorr = datetime.timedelta(0)

     start_dt = start_dt - tzcorr
     end_dt = end_dt - tzcorr

    start_string = start_dt.strftime('%Y%m%d')
    end_string = end_dt.strftime('%Y%m%d')
    
    # now, if we have a start time, append it
    if starttime_dt:
        start_string = '{0}T{1}'.format(start_string,start_dt.astimezone(pytz.utc).strftime("%H%M00Z"))

    if endtime_dt:
        end_string = '{0}T{1}'.format(end_string,end_dt.astimezone(pytz.utc).strftime("%H%M00Z"))
    
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
    event=event.format(summary, start_string, end_string, the_gig.details, the_gig.address, the_url)
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
            
