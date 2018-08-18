#
#  caldav server class for Gig-o-Matic 2
#
# Aaron Oppenheimer
# 29 March 2014
#
from google.appengine.ext import ndb
import cloudstorage as gcs
from google.appengine.api import app_identity

from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2

import gig
import assoc
import band
import plan

import datetime
import logging
from pytz.gae import pytz

def make_cal_header(the_title):
    header = """BEGIN:VCALENDAR
PRODID:-//Gig-o-Matic//Gig-o-Matic 2//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{0}
X-WR-CALDESC:{1}
REFRESH-INTERVAL;VALUE=DURATION:PT2H
X-PUBLISHED-TTL:PT2H
"""

# X-WR-TIMEZONE:{1}

    return header.format(the_title, "Gig-o-Matic calendar for {0}".format(the_title))

def make_cal_footer():
    return "END:VCALENDAR\n"

def make_event(the_gig, the_band, title_format=u'{0}', details_format=u'{0}', show_url=True, force_set_time=False):
    summary = the_gig.title

    # make real gig start time, assuming everything is in local time
    start_dt = the_gig.date
    if the_gig.enddate:
        end_dt = the_gig.enddate
    else:
        end_dt = start_dt

    starttime_dt = None
    endtime_dt = None
    if the_gig.calltime and not force_set_time:
        try:
            starttime_dt = datetime.datetime.strptime(the_gig.calltime, "%I:%M%p")
        except:
            try:
                starttime_dt = datetime.datetime.strptime(the_gig.calltime, "%H:%M")
            except:
                starttime_dt = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0)

    if starttime_dt is None and the_gig.settime: # only use the set time if there's no call time
        try:
            starttime_dt = datetime.datetime.strptime(the_gig.settime, "%I:%M%p")
        except:
            try:
                starttime_dt = datetime.datetime.strptime(the_gig.settime, "%H:%M")
            except:
                starttime_dt = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0)

    if the_gig.endtime:
        try:
            endtime_dt = datetime.datetime.strptime(the_gig.endtime, "%I:%M%p")
        except:
            try:
                endtime_dt = datetime.datetime.strptime(the_gig.endtime, "%H:%M")
            except:
                pass

    if starttime_dt is not None and endtime_dt is None:
        # no end time - use the start time if there is one, plus 1 hour
        endtime_dt = starttime_dt + datetime.timedelta(hours=1)

    if starttime_dt:
        start_dt = datetime.datetime.combine(start_dt, starttime_dt.time())

    if endtime_dt and end_dt:
        end_dt = datetime.datetime.combine(end_dt, endtime_dt.time())

    # do the setup so we can do timezone math
    if the_band.timezone:
        zone=pytz.timezone(the_band.timezone)
        start_dt=zone.localize(start_dt)
        end_dt=zone.localize(end_dt)

    else:
        start_dt = start_dt.replace(tzinfo=pytz.utc)
        end_dt = end_dt.replace(tzinfo=pytz.utc)

    if end_dt < start_dt:
        end_dt = end_dt+ datetime.timedelta(days=1)

    start_string = start_dt.astimezone(pytz.utc).strftime('%Y%m%d')
    end_string = end_dt.astimezone(pytz.utc).strftime('%Y%m%d')

    # now, if we have a start time, append it
    if starttime_dt is not None:
        start_string = '{0}T{1}'.format(start_string,
                                        start_dt.astimezone(pytz.utc).strftime("%H%M00Z"))

    if endtime_dt is not None:
        end_string = '{0}T{1}'.format(end_string,
                                      end_dt.astimezone(pytz.utc).strftime("%H%M00Z"))

    if show_url:
        the_url = 'http://www.gig-o-matic.com/gig_info.html?gk={0}'.format(the_gig.key.urlsafe())
    else:
        the_url = ''

    event = u"""BEGIN:VEVENT
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
    the_details = details_format.format(
                            '{0}\\n\\n{1}'.format(
                                the_gig.details.encode('ascii','ignore').replace('\r\n', '\\n'),
                                the_gig.setlist.encode('ascii','ignore').replace('\r\n', '\\n')
                            )
                        )

    event = event.format(title_format.format(summary), start_string, end_string,
                         the_details,
                         the_gig.address, the_url)
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

        the_band_key = ndb.Key(urlsafe=bk)
        the_band = the_band_key.get()

        calfeed = None
        if the_band.band_cal_feed_dirty is False:
            calfeed = get_calfeed_for_key("b",the_band.key)

        if calfeed is None:
            the_band.band_cal_feed_dirty = False
            the_band.put()

            calfeed = u'{0}'.format(make_cal_header(the_band.name))

            all_gigs = gig.get_gigs_for_band_keys(the_band_key)
            for a_gig in all_gigs:
                if a_gig.is_confirmed and not a_gig.hide_from_calendar:
                    calfeed = u'{0}{1}'.format(calfeed, make_event(a_gig, the_band))

            calfeed = u'{0}{1}'.format(calfeed, make_cal_footer())
            store_calfeed_for_key("b",the_band.key,calfeed)
        self.response.write(calfeed)

    def post(self):
        print 'got post request'


class PublicBandGigRequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):

        bk = kwargs['bk']

        the_band_key = ndb.Key(urlsafe=bk)
        the_band = the_band_key.get()

        calfeed = None
        if the_band.pub_cal_feed_dirty is False:
            calfeed = get_calfeed_for_key("p",the_band.key)

        if calfeed is None:
            logging.info("band cal feed is dirty")
            the_band.pub_cal_feed_dirty = False
            the_band.put()

            calfeed = u'{0}'.format(make_cal_header(the_band.name))

            all_gigs = gig.get_gigs_for_band_keys(the_band_key, show_only_public=True)
            for a_gig in all_gigs:
                if a_gig.is_confirmed and not a_gig.hide_from_calendar:
                    calfeed = u'{0}{1}'.format(calfeed, make_event(a_gig, the_band, show_url=False, force_set_time=True))

            calfeed = u'{0}{1}'.format(calfeed, make_cal_footer())
            store_calfeed_for_key("p",the_band.key,calfeed)
        self.response.write(calfeed)

    def post(self):
        print 'got post request'


class MemberRequestHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):

        mk = kwargs['mk']

        the_member_key = ndb.Key(urlsafe=mk)
        the_member = the_member_key.get()
        
        calfeed = None
        if the_member.cal_feed_dirty is False:
            calfeed = get_calfeed_for_key("m",the_member.key)

        if calfeed is None:
            logging.info("member cal feed is dirty")
            the_member.cal_feed_dirty = False
            the_member.put()

            # construct the calendar feed, since it may have changed lately

            calfeed = u'{0}'.format(make_cal_header(the_member.name))

            the_bands = assoc.get_confirmed_bands_of_member(the_member)

            for a_band in the_bands:
                a_band_name = a_band.shortname if a_band.shortname else a_band.name
                all_gigs = gig.get_gigs_for_band_keys(a_band.key, show_past=True)
                for a_gig in all_gigs:
                    if not a_gig.is_canceled and not a_gig.hide_from_calendar: # and not a_gig.is_archived:
                        the_plan = plan.get_plan_for_member_key_for_gig_key(the_member_key, a_gig.key)
                        if the_plan:
                            # check member preferences
                            # include gig if member wants to see all, or if gig is confirmed
                            if a_gig.is_confirmed or \
                                the_member.preferences.calendar_show_only_confirmed == False:
                                # incude gig if member wants to see all, or if has registered
                                # as maybe or definitely:
                                if (the_plan.value > 0 and the_plan.value <= 3) or \
                                    (the_member.preferences.calendar_show_only_committed == False):
                                    if a_gig.is_confirmed:
                                        confstr = u'CONFIRMED!'
                                    else:
                                        confstr = u'(not confirmed)'
                                    calfeed = u'{0}{1}'.format(calfeed, \
                                        make_event(a_gig, a_band, \
                                        title_format=u'{0}:{{0}} {1}'.format(a_band_name, confstr)))

            calfeed = u'{0}{1}'.format(calfeed, make_cal_footer())
            store_calfeed_for_key("m",the_member.key,calfeed)
        self.response.write(calfeed)

    def post(self):
        print 'got post request'


def store_calfeed_for_key(prefix, the_key, the_feed):

    bucket_name = os.environ.get('BUCKET_NAME',
                           app_identity.get_default_gcs_bucket_name())

    # self.response.headers['Content-Type'] = 'text/plain'
    # self.response.write('Demo GCS Application running from Version: '
    #                   + os.environ['CURRENT_VERSION_ID'] + '\n')
    # self.response.write('Using bucket name: ' + bucket_name + '\n\n')

    filename = "/{0}/{1}{2}{3}".format(bucket_name,prefix,"cal-",the_key.urlsafe())
    # self.response.write('Creating file %s\n' % filename)

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(filename,
                      'w',
                      content_type='text/plain',
                      retry_params=write_retry_params)
    gcs_file.write(the_feed.encode('UTF-8'))
    gcs_file.close()
    return the_feed

def get_calfeed_for_key(prefix, the_key):
    bucket_name = os.environ.get('BUCKET_NAME',
                           app_identity.get_default_gcs_bucket_name())

    filename = "/{0}/{1}{2}{3}".format(bucket_name,prefix,"cal-",the_key.urlsafe())

    gcs_file = None

    try:
        gcs_file = gcs.open(filename)
    except:
        gcs_file = None

    if gcs_file:
        feed = gcs_file.read()
        gcs_file.close()
        logging.info("found file")
    else:
        feed = None
        logging.info("did not find file")

    return feed



class HelpHandler(BaseHandler):
    """Handle a request for help"""

    @user_required
    def get(self):
        """ get handler for help page """
        self._make_page(the_user=self.user)

    def _make_page(self, the_user):
        """ construct page for help """

        template_args = {
            'member' : the_user
        }
        self.render_template('calhelp.html', template_args)


