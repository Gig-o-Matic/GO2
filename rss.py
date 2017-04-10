#
#  rss handling for Gig-o-Matic 2
#
# Aaron Oppenheimer
# 10 April 2017
#
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
import logging
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

import gig
import band

import datetime
from pytz.gae import pytz


def make_gig_feed(the_band):
    feed = None
    return feed


#####
#
# Page Handlers
#
#####

class MakeRssHandler(BaseHandler):
    """Handle a CalDav request"""

    def get(self, *args, **kwargs):

        bucket_name = os.environ.get('BUCKET_NAME',
                               app_identity.get_default_gcs_bucket_name())

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Demo GCS Application running from Version: '
                          + os.environ['CURRENT_VERSION_ID'] + '\n')
        self.response.write('Using bucket name: ' + bucket_name + '\n\n')

        filename = "/{0}/{1}".format(bucket_name,"test.txt")
        self.response.write('Creating file %s\n' % filename)

        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        gcs_file = gcs.open(filename,
                          'w',
                          content_type='text/plain',
                          options={'x-goog-meta-foo': 'foo',
                                   'x-goog-meta-bar': 'bar'},
                          retry_params=write_retry_params)
        gcs_file.write('abcde\n')
        gcs_file.write('f'*1024*4 + '\n')
        gcs_file.close()
        # self.tmp_filenames_to_clean_up.append(filename)


        self.response.write('Listbucket result:\n')

        # Production apps should set page_size to a practical value.
        page_size = 1
        stats = gcs.listbucket("/"+bucket_name, max_keys=page_size)
        while True:
            count = 0
            for stat in stats:
                count += 1
                self.response.write(repr(stat))
                self.response.write('\n')

            if count != page_size or count == 0:
                break
            stats = gcs.listbucket(
                filename, max_keys=page_size, marker=stat.filename)

        self.response.write('\n\n')


        self.response.write('Abbreviated file content (first line and last 1K):\n')

        gcs_file = gcs.open(filename)
        self.response.write(gcs_file.readline())
        gcs_file.seek(-1024, os.SEEK_END)
        self.response.write(gcs_file.read())
        gcs_file.close()

