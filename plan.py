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
    section = ndb.KeyProperty()

    def set_comment(self, the_comment):
        self.comment=the_comment;
        self.put()

def new_plan(the_gig, the_member, value):
    """ associate a gig and a member """
    the_plan = Plan(parent=the_gig.key, member=the_member.key, value=value, comment="", section=member.default_section_for_band_key(the_member, the_gig.key.parent()))
    the_plan.put()
    return the_plan

def get_plan_from_id(the_gig, id):
    """ Return plan object by id; needs the key for the parent, which is the band for this plan"""
    return Plan.get_by_id(int(id), parent=the_gig.key)

def get_plans_for_gig(the_gig):
    """ Return plan objects by gig"""
    plan_query = Plan.query(ancestor=the_gig.key)
    plans = plan_query.fetch()
    return plans

def get_plan_for_member_for_gig(the_member, the_gig):
    plan_query = Plan.query(Plan.member==the_member.key, ancestor=the_gig.key)
    plans = plan_query.fetch()
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

def update_plan_section_key(the_plan, the_section_key):
    the_plan.section=the_section_key
    the_plan.put()

def delete_plans_for_gig(the_gig):
    """ A gig is being deleted, so forget everyone's plans about it """
    plan_query = Plan.query(ancestor=the_gig.key)
    plans = plan_query.fetch()
    for a_plan in plans:
        a_plan.key.delete()
        
def delete_plans_for_member_for_band_key(the_member, the_band_key):
    """ A gig is being deleted, so forget everyone's plans about it """
    plan_query = Plan.query(Plan.member==the_member.key, ancestor=the_band_key)
    plans = plan_query.fetch(keys_only=True)
    ndb.delete_multi(plans)
        
class UpdatePlan(webapp2.RequestHandler):
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        the_value=int(self.request.get("val", 0))
        the_plan_key=self.request.get("pk",'0')
        
        if (the_plan_key=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_key).get()
        
        if (the_plan is not None):
            update_plan(the_plan, the_value)
        else:
            pass # todo figure out why there was no plan
        
class UpdatePlanComment(webapp2.RequestHandler):
    def post(self):
        """post handler - if a comment is edited, update the database"""

        the_value=self.request.get("val", "")
        the_plan_key=self.request.get("pk",'0')
        
        if (the_plan_key=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_key).get()
        
        if (the_plan is not None):
            update_plan_comment(the_plan, the_value)
        else:
            pass # todo figure out why there was no plan

class UpdatePlanSection(webapp2.RequestHandler):
    def post(self):
        """post handler - if a section is edited, update the database"""
        
        the_section_keyurl=self.request.get("sk", '0')
        the_plan_keyurl=self.request.get("pk",'0')
        
        if (the_plan_keyurl=='0' or the_section_keyurl=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_keyurl).get()
        the_section_key=ndb.Key(urlsafe=the_section_keyurl)
        
        if (the_plan is not None):
            update_plan_section_key(the_plan, the_section_key)
        else:
            pass # todo figure out why there was no plan
        
