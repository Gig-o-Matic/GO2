#
# plan class for Gig-o-Matic 2 - links members to gigs
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from member import *
from debug import *

#
# class for plan
#
class Plan(ndb.Model):
    """ Models a gig-o-matic plan """
    member = ndb.KeyProperty()
    value = ndb.IntegerProperty()

def new_plan(gig, member, value):
    """ associate a gig and a member """
    the_plan = Plan(parent=gig.key, member=member.key, value=value)
    the_plan.put()

def get_plans_for_gig(gig):
    """ Return plan objects by gig"""
    plan_query = Plan.query(ancestor=gig.key)
    plans = plan_query.fetch()
    debug_print('get_plans_for_gig: got {0} plans for gig key id {1} ({2})'.format(len(plans),gig.key.id(),gig.title))
    return plans

