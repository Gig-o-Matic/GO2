#
# plan class for Gig-o-Matic 2 - links members to gigs
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from debug import debug_print
import webapp2

import gig
import band
import member

#
# class for plan
#
class Plan(ndb.Model):
    """ Models a gig-o-matic plan """
    member = ndb.KeyProperty()
    value = ndb.IntegerProperty()
    comment = ndb.StringProperty(indexed=False)

    def set_comment(self, the_comment):
        self.comment=the_comment;
        self.put()

def new_plan(the_gig, the_member, value):
    """ associate a gig and a member """
    the_plan = Plan(parent=the_gig.key, member=the_member.key, value=value, comment="")
    the_plan.put()
    return the_plan

def get_plan_from_id(the_gig, id):
    """ Return plan object by id; needs the key for the parent, which is the band for this plan"""
    debug_print('get_plan_from_id looking for id {0}'.format(id))
    return Plan.get_by_id(int(id), parent=the_gig.key)

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
        # no plan? make a new one
        return new_plan(the_gig, the_member, 0)

def update_plan(the_plan, the_value):
    the_plan.value=the_value
    the_plan.put()

def update_plan_comment(the_plan, the_value):
    the_plan.comment=the_value
    the_plan.put()

def delete_plans_for_gig(the_gig):
    """ A gig is being deleted, so forget everyone's plans about it """
    plan_query = Plan.query(ancestor=the_gig.key)
    plans = plan_query.fetch()
    for a_plan in plans:
        a_plan.key.delete()
        
        
class UpdatePlan(webapp2.RequestHandler):
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'UPDATE_PLAN POST HANDLER'
        the_value=int(self.request.get("val", 0))
        the_plan_key=self.request.get("pk",'0')
        
        if (the_plan_key=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_key).get()
        
        if (the_plan is not None):
            update_plan(the_plan, the_value)
        else:
            pass # todo figure out why there was no plan
        print 'FOUND plan {0}'.format(the_plan.key.id())
        
class UpdatePlanComment(webapp2.RequestHandler):
    def post(self):
        """post handler - if a comment is edited, update the database"""
        print 'Update_Plan_Comment post handler'
        the_value=self.request.get("val", "")
        the_plan_key=self.request.get("pk",'0')
        
        if (the_plan_key=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_key).get()
        
        if (the_plan is not None):
            update_plan_comment(the_plan, the_value)
        else:
            pass # todo figure out why there was no plan
        print 'FOUND plan {0}'.format(the_plan.key.id())
        
