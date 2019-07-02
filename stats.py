#
#  stats class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 29 Jan 2014
#
from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
from debug import *

import assoc
import gig
import band
import member

import logging
import json
import datetime

def stats_key(member_name='stats_key'):
    """Constructs a Datastore key for a Stats entity with stats_name."""
    return ndb.Key('stats', stats_name)

class BandStats(ndb.Model):
    """ class to hold statistics """
    band = ndb.KeyProperty()
    date = ndb.DateProperty(auto_now_add=True)
    number_members = ndb.IntegerProperty(default=0)
    number_upcoming_gigs = ndb.IntegerProperty(default=0)
    number_gigs_created_today = ndb.IntegerProperty( default = 0)
    number_emails_sent_today = ndb.IntegerProperty(default = 0)
    
def get_band_stats(the_band_key, today=False):
    """ Return all the stats we have for a band """
    args = [
        BandStats.band==the_band_key
    ]

    if today:
        date = datetime.datetime.today() - datetime.timedelta(days=1)
        args.append( BandStats.date > date )

    stats_query = BandStats.query( *args).order(-BandStats.date)
    the_stats = stats_query.fetch(limit=30)

    return the_stats

def get_today_stats(the_band_key):
    today_stats = get_band_stats(the_band_key = the_band_key, today = True)
    if len(today_stats) == 0:
        the_stats = BandStats(band=the_band_key)
    else:
        the_stats = today_stats[0]
    return the_stats

def make_band_stats(the_band_key):
    """ make a stats object for a band key and return it """
    the_stats = get_today_stats(the_band_key)

    all_member_keys = assoc.get_member_keys_of_band_key(the_band_key)
    the_stats.number_members = len(all_member_keys)
    logging.info("band {0} stats: {1} members".format(the_band_key.id(), the_stats.number_members))
    
    all_gigs = gig.get_gigs_for_band_keys(the_band_key, keys_only=True)
    the_stats.number_upcoming_gigs = len(all_gigs)
    logging.info("band {0} stats: {1} upcoming gigs".format(the_band_key.id(), the_stats.number_upcoming_gigs))
    
    today_gigs = gig.get_gigs_for_creation_date(the_band_key, the_stats.date)
    the_stats.number_gigs_created_today = len(today_gigs)
    
    the_stats.put()

def update_band_gigs_created_stats(the_band_key):
    the_stats = get_today_stats(the_band_key)
    the_stats.number_gigs_created_today += 1
    the_stats.put()

def update_band_email_stats(the_band_key, number_sent):
    the_stats = get_today_stats(the_band_key)
    the_stats.number_emails_sent_today += number_sent
    the_stats.put()

def delete_band_stats(the_band_key):
    """ delete all stats for a band """
    stats_query = BandStats.query( BandStats.band==the_band_key)
    the_stats = stats_query.fetch(keys_only=True)
    ndb.delete_multi(the_stats)


#####
#
# Page Handlers
#
#####

class StatsPage(BaseHandler):
    """Page for showing stats"""

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):

        the_member_keys = member.get_all_members(order=False, keys_only=True, verified_only=True)

        the_bands = band.get_all_bands()

        stats=[]
        inactive_bands=[]
        for a_band in the_bands:
            is_band_active=False
                
            a_stat = get_band_stats(a_band.key, today=False)
            
            the_count_data=[]

            if len(a_stat) > 0:
                s = a_stat[0]
                if s.number_upcoming_gigs > 0:
                    is_band_active = True
                for s in a_stat:
                    print("EMAIL: {0} {1}".format(s.number_emails_sent_today,s.number_gigs_created_today))
                    the_count_data.append([s.date.year, s.date.month-1, s.date.day, s.number_members, s.number_upcoming_gigs, s.number_gigs_created_today, s.number_emails_sent_today])

                if is_band_active:
                    the_count_data_json=json.dumps(the_count_data)
                    stats.append([a_band, the_count_data_json])
                else:
                    inactive_bands.append(a_band)
        
        template_args = {
            'the_stats' : stats,
            'num_members' : len(the_member_keys),
            'num_bands' : len(the_bands),
            'num_active_bands' : len(the_bands) - len(inactive_bands),
            'inactive_bands' : inactive_bands
        }
        self.render_template('stats.html', template_args)


##########
#
# auto generate stats
#
##########
class AutoGenerateStats(BaseHandler):
    """ automatically generate statistics """
    def get(self):
        the_band_keys = band.get_all_bands(keys_only = True)
        for band_key in the_band_keys:
            make_band_stats(band_key)