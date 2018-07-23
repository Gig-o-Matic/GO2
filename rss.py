#
#  rss handling for Gig-o-Matic 2
#
# Aaron Oppenheimer
# 10 April 2017
#
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models
from google.appengine.api.taskqueue import taskqueue

import webapp2
import logging
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

import gig
import band
import member

import datetime
from pytz.gae import pytz
import pickle

def make_gig_feed(the_band):

    the_gigs = gig.get_gigs_for_band_keys(the_band.key, show_canceled=False, show_only_public=True, show_past=False, confirmed_only=True, start_date=datetime.datetime.now())
    feed = u"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
"""

    feed=u"{0}\n<title>{1} Gigs</title>".format(feed, the_band.name)
    feed=u"{0}\n<link>{1}{2}</link>".format(feed, "http://www.gig-o-matic.com/feeds/",the_band.key.urlsafe())
    feed=u"{0}\n<description>{1} Gigs</description>".format(feed, the_band.name)

    for a_gig in the_gigs:
        feed=u"{0}\n<item>".format(feed)
        feed=u"{0}\n<title>{1}</title>".format(feed, a_gig.title)
        feed=u'{0}\n<guid isPermaLink="false">{1}</guid>'.format(feed, a_gig.key.urlsafe())
        if a_gig.contact:
            the_date = member.format_date_for_member(a_gig.contact.get(),a_gig.date,"long")
        else:
            the_date = a_gig.date

        if a_gig.settime:
            the_time = u' - {0}'.format(a_gig.settime)
        else:
            the_time = u''

        if a_gig.rss_description:
            the_desc = a_gig.rss_description
        else:
            the_desc = ''

        feed=u"{0}\n<description><![CDATA[{1}{2}\n\n{3}]]></description>".format(feed, the_date, the_time, the_desc)
        # feed=u"{0}\n<description>{1}{2}\n\n{3}</description>".format(feed, the_date, the_time, a_gig.rss_description)
        feed=u"{0}\n</item>".format(feed)
    feed=u"{0}{1}".format(feed,"""
</channel>
</rss>
""")

    return feed


def store_feed_for_band_key(the_band_key, the_feed):

    bucket_name = os.environ.get('BUCKET_NAME',
                           app_identity.get_default_gcs_bucket_name())

    # self.response.headers['Content-Type'] = 'text/plain'
    # self.response.write('Demo GCS Application running from Version: '
    #                   + os.environ['CURRENT_VERSION_ID'] + '\n')
    # self.response.write('Using bucket name: ' + bucket_name + '\n\n')

    filename = "/{0}/{1}{2}".format(bucket_name,"rss-",the_band_key.urlsafe())
    # self.response.write('Creating file %s\n' % filename)

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(filename,
                      'w',
                      content_type='text/plain',
                      retry_params=write_retry_params)
    gcs_file.write(the_feed.encode('UTF-8'))
    gcs_file.close()
    return the_feed

def get_feed_for_band_key(the_band_key):
    bucket_name = os.environ.get('BUCKET_NAME',
                           app_identity.get_default_gcs_bucket_name())

    filename = "/{0}/{1}{2}".format(bucket_name,"rss-",the_band_key.urlsafe())

    gcs_file = None

    try:
        gcs_file = gcs.open(filename)
    except:
        gcs_file = None

    if gcs_file:
        feed = gcs_file.read()
        gcs_file.close()
    else:
        feed = ""

    return feed

def make_rss_feed_for_band(the_band):
    the_params = pickle.dumps({'the_band_key': the_band.key})

    task = taskqueue.add(
            url='/make_rss_feed_handler',
            params={'the_params': the_params
            })

class MakeRssFeedHandler(webapp2.RequestHandler):

    def post(self):
        the_params = pickle.loads(self.request.get('the_params'))
        the_band_key = the_params['the_band_key']
        the_band = the_band_key.get()
        store_feed_for_band_key(the_band.key, make_gig_feed(the_band))

#####
#
# Page Handlers
#
#####


class GetRssHandler(BaseHandler):
    """Handle an RSS request"""

    def get(self, *args, **kwargs):

        the_band_keyurl = kwargs['bk']

        if the_band_keyurl is None:
            return # figure out what to do
        else:
            the_band = ndb.Key(urlsafe = the_band_keyurl).get()

        feed = get_feed_for_band_key(the_band.key)

        self.response.content_type = 'application/rss+xml'
        self.response.write('{0}\n'.format(feed))




