#
# plan class for Gig-o-Matic 2 - links members to gigs
#
# Aaron Oppenheimer
# 24 August 2013
#

import debug
from google.appengine.ext import ndb
from debug import debug_print
import webapp2

import gig
import band
import member
import assoc
import datetime
import logging

plan_text = ["No Plan", "Definitely", "Probably", "Don't Know", "Probably Not", "Can't Do It", "Not Interested"]

#
# class for plan
#
class Plan(ndb.Model):
    """ Models a gig-o-matic plan """
    member = ndb.KeyProperty()
    value = ndb.IntegerProperty()
    feedback_value = ndb.IntegerProperty()
    comment = ndb.StringProperty(indexed=False)
    section = ndb.KeyProperty()
    last_update = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def lquery(cls, *args, **kwargs):
        if debug.DEBUG:
            print('{0} query'.format(cls.__name__))
        return cls.query(*args, **kwargs)

    def set_comment(self, the_comment):
        self.comment=the_comment;
        self.put()

def new_plan(the_gig, the_member, value):
    """ associate a gig and a member """
    the_plan = Plan(parent=the_gig.key, member=the_member.key, value=value, comment="", section=None)
    the_plan.put()

    return the_plan

def get_plan_from_id(the_gig, id):
    """ Return plan object by id; needs the key for the parent, which is the band for this plan"""
    return Plan.get_by_id(int(id), parent=the_gig.key)

def get_plans_for_gig_key(the_gig_key, keys_only = False):
    """ Return plan objects by gig"""
    plan_query = Plan.lquery(ancestor=the_gig_key)
    plans = plan_query.fetch(keys_only=keys_only)
    return plans

def get_plan_for_member_key_for_gig_key(the_member_key, the_gig_key):
    plan_query = Plan.lquery(Plan.member==the_member_key, ancestor=the_gig_key)
    plans = plan_query.fetch()
    if len(plans)>1:
        logging.error("gig/member with multiple plans! gk={0} mk={1}".format(the_gig_key.urlsafe(),the_member_key.urlsafe()))
#         return None #todo what to do if there's more than one plan        

        # more than one plan! Just delete the others - not sure how they got here
        the_plan = plans[0]
        delplan_keys = [p.key for p in plans[1:]]
        ndb.delete_multi(delplan_keys)
        return the_plan
    if len(plans)>0:
        return plans[0]
    else:
        # no plan? make a new one
        return new_plan(the_gig_key.get(), the_member_key.get(), 0)

def get_plan_for_member_for_gig(the_member, the_gig):
    return get_plan_for_member_key_for_gig_key(the_member_key=the_member.key, the_gig_key=the_gig.key)

def get_recent_changes_for_band_key(the_band_key, the_time_delta_days=1, keys_only=False):
    "find plans for gigs belonging to a band key that have changed lately"
    plan_query = Plan.lquery(Plan.last_update>(datetime.datetime.now() - datetime.timedelta(days=the_time_delta_days)), ancestor=the_band_key)
    plans = plan_query.fetch(keys_only=keys_only)
    return plans
    
def update_plan(the_plan, the_value):
    the_plan.value=the_value
    the_plan.put()

def update_plan_feedback(the_plan, the_value):
    the_plan.feedback_value=the_value
    the_plan.put()

def update_plan_comment(the_plan, the_value):
    the_plan.comment=the_value
    the_plan.put()

def update_plan_section_key(the_plan, the_section_key):
    the_plan.section=the_section_key
    the_plan.put()

def remove_section_from_plans(the_section_key):
    """ if any plans have this section key, set the section to None """
    plan_query = Plan.lquery(Plan.section==the_section_key)
    the_plans = plan_query.fetch()
    for the_plan in the_plans:
        the_plan.section=None
    ndb.put_multi(the_plans)

def delete_plans_for_gig_key(the_gig_key):
    """ A gig is being deleted, so forget everyone's plans about it """
    plan_query = Plan.lquery(ancestor=the_gig_key)
    the_plan_keys = plan_query.fetch(keys_only=True)
    ndb.delete_multi(the_plan_keys)
        
def delete_plans_for_member_key_for_band_key(the_member_key, the_band_key):
    """ A gig is being deleted, so forget everyone's plans about it """
    plan_query = Plan.lquery(Plan.member==the_member_key, ancestor=the_band_key)
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
        
class UpdatePlanFeedback(webapp2.RequestHandler):
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        the_value=int(self.request.get("val", 0))
        the_plan_key=self.request.get("pk",'0')
        
        if (the_plan_key=='0'):
            return #todo figure out what to do if no plan passed in
            
        the_plan=ndb.Key(urlsafe=the_plan_key).get()
        
        if (the_plan is not None):
            update_plan_feedback(the_plan, the_value)
        else:
            pass # todo figure out why there was no plan

        strings = band.get_feedback_strings(the_plan.key.parent().parent().get())

        if the_value == 0:
            resp = ''            
        elif the_value <= len(strings):
            resp = strings[the_value-1]
        self.response.write(resp)

class UpdatePlanComment(webapp2.RequestHandler):
    def post(self):
        """post handler - if a comment is edited, update the database"""

        the_value=self.request.get("value", "")
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
        
