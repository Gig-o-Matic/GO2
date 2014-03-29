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

def make_event():
    event="""BEGIN:VEVENT
DTSTART:20140329T210000Z
DTEND:20140329T220000Z
DTSTAMP:20140329T155645Z
UID:3jba27qkcfjmf9elvfs909fgdk@google.com
CREATED:20140329T154445Z
DESCRIPTION:
LAST-MODIFIED:20140329T154445Z
LOCATION:
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:blah blah blag
TRANSP:OPAQUE
END:VEVENT
"""
    return event

#####
#
# Page Handlers
#
#####

class RequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self):    
        print 'got get request'
        print '\n\n{0}\n\n'.format(self.request.url)
        info = '{0}'.format(make_cal_header())
        info = '{0}{1}'.format(info, make_event())
        info = '{0}{1}'.format(info, make_cal_footer())
        self.response.write(info)
            
    def post(self):    
        print 'got post request'
            
