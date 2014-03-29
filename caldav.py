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

def make_cal_header():
    header="""BEGIN:VCALENDAR
PRODID:-//Gig-o-Matic//Gig-o-Matic 2//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{0}
X-WR-TIMEZONE:{1}
X-WR-CALDESC:{2}
"""
    return header.format("testband","-5","Calendar for testband")

def make_cal_footer():
    return "END:VCALENDAR\n"

def make_event(the_gig):
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
    dtend = dtstart

    event="""BEGIN:VEVENT
DTSTART:{1}
DTEND:{2}
DESCRIPTION:
LOCATION:
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:{0}
TRANSP:OPAQUE
END:VEVENT
"""
    event=event.format(summary, dtstart, dtend)
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
            
        print '\n\n{0}\n\n'.format(bk)

        info = '{0}'.format(make_cal_header())

        all_gigs = gig.get_gigs_for_band_keys(ndb.Key(urlsafe=bk))
        for a_gig in all_gigs:
            info = '{0}{1}'.format(info, make_event(a_gig))

        info = '{0}{1}'.format(info, make_cal_footer())
        self.response.write(info)
            
    def post(self):    
        print 'got post request'
            
