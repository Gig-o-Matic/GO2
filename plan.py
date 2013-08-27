#
# plan class for Gig-o-Matic 2 - links members to gigs
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from debug import debug_print

#
# class for plan
#
class Plan(ndb.Model):
    """ Models a gig-o-matic plan """
    member = ndb.KeyProperty()
    value = ndb.IntegerProperty()

def new_plan(the_gig, the_member, value):
    """ associate a gig and a member """
    the_plan = Plan(parent=the_gig.key, member=the_member.key, value=value)
    the_plan.put()

def get_plans_for_gig(the_gig):
    """ Return plan objects by gig"""
    plan_query = Plan.query(ancestor=the_gig.key)
    plans = plan_query.fetch()
    debug_print('get_plans_for_gig: got {0} plans for gig key id {1} ({2})'.format(len(plans),the_gig.key.id(),the_gig.title))
    return plans

def get_plan_for_member_for_gig(the_member, the_gig):
    plan_query = Plan.query(Plan.member==the_member.key, ancestor=the_gig.key)
    plans = plan_query.fetch()
    debug_print('get_plans_for_gig: got {0} plans for gig key id {1} ({2})'.format(len(plans),the_gig.key.id(),the_gig.title))
    if len(plans)>1:
        return None #todo what to do if there's more than one plan
        
    if len(plans)>0:
        return plans[0]
    else:
        return None
