#
# gig class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#
from google.appengine.api import users
from google.appengine.ext import ndb
import webapp2
from jinja2env import jinja_environment as je

import member
import band
import assoc
import plan

from debug import debug_print
import datetime

#
# class for gig
#
class Gig(ndb.Model):
    """ Models a gig-o-matic gig """
    title = ndb.TextProperty()
    contact = ndb.UserProperty()
    details = ndb.TextProperty()
    date = ndb.DateProperty()
    call = ndb.TimeProperty()

#
# Functions to make and find gigs
#

def new_gig(the_band, title, contact=None, details="", date=None, call=None):
    """ Make and return a new gig """
    the_gig = Gig(parent=the_band.key, title=title, contact=contact, details=details, date=date, call=call)
    the_gig.put()
    debug_print('new_gig: added new gig: {0} on {1}'.format(title,str(date)))
    return the_gig
                
def get_gig_from_key(key):
    """ Return gig objects by key"""
    return key.get()
    
def get_gig_from_id(the_band, id):
    """ Return gig object by id; needs the key for the parent, which is the band for this gig"""
    debug_print('get_gig_from_id looking for id {0}'.format(id))
    return Gig.get_by_id(int(id), parent=the_band.key)
    
def get_gigs_for_band(the_band,num=None):
    """ Return gig objects by band"""
    gig_query = Gig.query(ancestor=the_band.key).order(Gig.date)
    the_gigs = gig_query.fetch(limit=num)
    debug_print('get_gigs_for_band: got {0} gigs for band key id {1} ({2})'.format(len(the_gigs),the_band.key.id(),the_band.name))
    return the_gigs
    
def get_gigs_for_band_for_dates(the_band,start_date, end_date):
    """ Return gig objects by band"""
    gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                  Gig.date <= end_date), \
                                  ancestor=the_band.key).order(Gig.date)
    gigs = gig_query.fetch()
    debug_print('get_gigs_for_band_for_dates: got {0} gigs for band key id {1} ({2})'.format(len(gigs),the_band.key.id(),the_band.name))
    return gigs

def get_band_and_gig(band_id, gig_id):
        # which band are we talking about?
        if band_id is None:
            debug_print('get_band_and_gig: no band id passed in!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        # find the gig we're interested in
        if gig_id is None:
            debug_print('get_band_and_gig: no gig id passed in!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        the_band=band.get_band_from_id(band_id) # todo more efficient if we include the band key?
        
        if the_band is None:
            debug_print('get_band_and_gig: did not find a band!')
            return (None, None) # todo figure out what to do if there's no ID passed in
            
        the_gig=get_gig_from_id(the_band, gig_id) # todo more efficient if we include the band key?
        
        if the_gig is None:
            debug_print('get_band_and_gig: did not find a gig!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        return (the_band, the_gig)

#
#
# Handlers
#
#

class InfoPage(webapp2.RequestHandler):
    def get(self):    
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)

    def make_page(self,user):
        debug_print('IN GIG_INFO {0}'.format(user.nickname()))
        
        the_member=member.get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(the_member)))
        
        if the_member is None:
            return # todo figure out what to do if we get this far and there's no member

        # which band are we talking about?
        band_id=self.request.get("band_id",None)
        if band_id is None:
            self.response.write('no band id passed in!')
            return # todo figure out what to do if there's no ID passed in

        # find the gig we're interested in
        gig_id=self.request.get("gig_id", None)
        if gig_id is None:
            self.response.write('no gig id passed in!')
            return # todo figure out what to do if there's no ID passed in

        the_band=band.get_band_from_id(band_id) # todo more efficient if we include the band key?
        
        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it

            
        the_gig=get_gig_from_id(the_band, gig_id) # todo more efficient if we include the band key?
        
        if the_gig is None:
            self.response.write('did not find a gig!')
            return # todo figure out what to do if we didn't find it
            
        debug_print('found gig object: {0}'.format(the_gig.title))

        member_plans=[]
        the_members=band.get_members_of_band(the_band)
        for a_member in the_members:
            if (a_member.nickname == user.nickname()):
                is_me = True
            else:
                is_me = False
            the_plan = plan.get_plan_for_member_for_gig(a_member, the_gig)
            member_plans.append( [a_member, the_plan, is_me] )
                    
        template = je.get_template('gig_info.html')
        self.response.write( template.render(
            title='Gig Info',
            member=the_member,
            logout_link=users.create_logout_url('/'),            
            gig=the_gig,
            band=the_band,
            member_plans=member_plans
        ) )        

class EditPage(webapp2.RequestHandler):
    def get(self):
        print 'GIG_EDIT GET HANDLER'
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)

    def make_page(self, user):
        debug_print('IN GIG_EDIT {0}'.format(user.nickname()))
        
        the_member=member.get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(the_member)))
        
        if the_member is None:
            return # todo figure out what to do if we get this far and there's no member

        if self.request.get("new",None) is not None:
            the_gig=None
            gig_id=0
            the_band=member.get_current_band(the_member)
            band_id=the_band.key.id()
            is_new=True
        else:
            band_id=self.request.get("band_id",None)
            gig_id=self.request.get("gig_id", None)
            the_band,the_gig=get_band_and_gig(band_id, gig_id)
            if the_band is None or the_gig is None:
                self.response.write('did not find a band or gig!')
                return # todo figure out what to do if we didn't find it
            debug_print('found gig object: {0}'.format(the_gig.title))
            is_new=False
                    
        template = je.get_template('gig_edit.html')
        self.response.write( template.render(
            title='Gig Edit',
            member=the_member,
            logout_link=users.create_logout_url('/'),            
            gig=the_gig,
            gig_id=gig_id,
            band_id=band_id,
            newgig_is_active=is_new
        ) )        

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'GIG_EDIT POST HANDLER'

        print str(self.request.arguments())

        band_id=int(self.request.get("band_id",None))
        gig_id=int(self.request.get("gig_id", None))
        
        print 'GIG ID IS {0}'.format(gig_id)
        
        if gig_id==0:
            the_band=band.get_band_from_id(band_id)
            the_gig=new_gig(the_band,'tmp')
            gig_id=the_gig.key.id()
        else:
            the_band,the_gig=get_band_and_gig(band_id, gig_id)

        if the_band is None or the_gig is None:
            self.response.write('did not find a band of gig!')
            return # todo figure out what to do if we didn't find it
       
        gig_title=self.request.get("gig_title",None)
        if gig_title is not None and gig_title != '':
            print 'got title {0}'.format(gig_title)
            the_gig.title=gig_title
        
        gig_details=self.request.get("gig_details",None)
        if gig_details is not None and gig_details != '':
            print 'got details {0}'.format(gig_details)
            the_gig.details=gig_details

        gig_date=self.request.get("gig_date",None)
        if gig_date is not None and gig_date != '':
            print 'got date {0}'.format(gig_date)
            the_gig.date=datetime.datetime.strptime(gig_date,'%m/%d/%Y').date()
            # todo validate form entry so date isn't bogus

        the_gig.put()            

        return self.redirect('/gig_info.html?band_id={0}&gig_id={1}'.format(band_id, gig_id))
                
class DeleteHandler(webapp2.RequestHandler):
    def get(self):
        print 'GIG_DELETE GET HANDLER'
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            band_id=self.request.get("band_id",None)
            gig_id=self.request.get("gig_id", None)
            the_band,the_gig=get_band_and_gig(band_id, gig_id)
            if the_band is None or the_gig is None:
                self.response.write('did not find a band or gig!')
            else:
                plan.delete_plans_for_gig(the_gig)            
                the_gig.key.delete()
            return self.redirect('/agenda.html')
                