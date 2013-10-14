"""

 gig class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2

import member
import band
import plan
import goemail
import gigarchive

from debug import debug_print
import datetime

#
# class for gig
#
class Gig(ndb.Model):
    """ Models a gig-o-matic gig """
    title = ndb.StringProperty()
    contact = ndb.UserProperty()
    details = ndb.TextProperty()
    setlist = ndb.TextProperty()
    date = ndb.DateProperty(auto_now_add=True)
    call = ndb.TimeProperty()
    archive_id = ndb.TextProperty()
    is_archived = ndb.ComputedProperty(lambda self: self.archive_id is not None)
#
# Functions to make and find gigs
#

def new_gig(the_band, title, date=None, contact=None, details="", setlist="", call=None):
    """ Make and return a new gig """
    if date is None:
        date = datetime.datetime.now()
    the_gig = Gig(parent=the_band.key, title=title, contact=contact, \
                    details=details, setlist=setlist, date=date, call=call)
    the_gig.put()
    debug_print('new_gig: added new gig: {0} on {1}'.format(title, str(date)))
    return the_gig
                
def get_gig_from_key(key):
    """ Return gig objects by key"""
    return key.get()
        
def get_gigs_for_bands(the_band_list, num=None, start_date=None):
    """ Return gig objects by band, ignoring past gigs """
        
    if (type(the_band_list) is not list):
        the_band_list = [the_band_list]

    if start_date:
        # correct the start date in case we're a non-UTC band (everyone, probably)
        # assumes that all the bands are in the same timezone
        test_band=the_band_list[0]
        print 'raw start date is {0}'.format(start_date)
        if test_band.time_zone_correction:
            # this band is in a non-UTC time zone!
            start_date=start_date+datetime.timedelta(hours=test_band.time_zone_correction)
            print 'tz start date is {0}'.format(start_date)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        print 'final start date is {0}'.format(start_date)
    
    all_gigs = []
    for a_band in the_band_list:
        if start_date is None:
            gig_query = Gig.query(Gig.is_archived==False, ancestor=a_band.key).order(Gig.date)
        else:
            gig_query = Gig.query(ndb.AND(Gig.date >= start_date, Gig.is_archived==False), \
                                  ancestor=a_band.key).order(Gig.date)
        the_gigs = gig_query.fetch()
        all_gigs.append(the_gigs)
        
    # now we have several lists of gigs - merge them
    if len(all_gigs) == 0:
        return None
    elif len(all_gigs) == 1:
        if num is None:
            return all_gigs[0]
        else:
            return all_gigs[:num]
    else:
        # merge the gigs
        sorted_gigs = []
        list1 = all_gigs.pop()    
        while all_gigs:
            list2 = all_gigs.pop()    
            while (list1 and list2):
                if (list1[0].date <= list2[0].date): # Compare both heads
                    item = list1.pop(0) # Pop from the head
                    sorted_gigs.append(item)
                else:
                    item = list2.pop(0)
                    sorted_gigs.append(item)

            # Add the remaining of the lists
            sorted_gigs.extend(list1 if list1 else list2)
            # now prepare to loop back
            list1 = sorted_gigs
            sorted_gigs = []

    sorted_gigs = list1
    print 'sorted gigs got {0}'.format(len(list1))

    if num is None:
        return list1
    else:
        return list1[:num]
    
    
    
def get_gigs_for_band_for_dates(the_band, start_date, end_date):
    """ Return gig objects by band, past gigs OK """
    gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                  Gig.date <= end_date), \
                                  ancestor=the_band.key).order(Gig.date)
    gigs = gig_query.fetch()
    debug_print('get_gigs_for_band_for_dates: got {0} gigs for \
                 band key id {1} ({2})'.format(len(gigs), \
                                                the_band.key.id(), \
                                                the_band.name))
    return gigs

def get_gigs_for_member_for_dates(the_member, start_date, end_date):
    """ return gig objects for the bands of a member """
    the_bands = member.get_confirmed_bands_of_member(the_member)
    all_gigs = []
    for a_band in the_bands:
        all_gigs.extend(get_gigs_for_band_for_dates(a_band, \
                                                    start_date, \
                                                    end_date))
    return all_gigs

def make_archive_for_gig_key(the_gig_key):
    """ makes an archive for a gig - files away all the plans, then delete them """
    
    archive_id = gigarchive.make_archive_for_gig_key(the_gig_key)
    if archive_id:
        the_gig = the_gig_key.get()
        if the_gig.archive_id:
            gigarchive.delete_archive(the_gig.archive_id)
        print 'gig: {0}'.format(the_gig)
        the_gig.archive_id = archive_id
        the_gig.put()

#
#
# Handlers
#
#

class InfoPage(BaseHandler):
    """ class to serve the gig info page """

    @user_required
    def get(self):    
        self._make_page(self.user)

    def _make_page(self, the_user):

        # find the gig we're interested in
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            self.response.write('no gig key passed in!')
            return # todo figure out what to do if there's no ID passed in

        gig_key = ndb.Key(urlsafe=gig_key_str)
        the_gig = gig_key.get()

        if the_gig is None:
            self.response.write('did not find a gig!')
            return # todo figure out what to do if we didn't find it
            
        if not the_gig.is_archived:
            the_band_key = the_gig.key.parent()

            the_member_keys = member.get_member_keys_of_band_key(the_band_key)
            
            the_plans = []
            
            need_empty_section = False
            for a_member_key in the_member_keys:
                a_member = a_member_key.get()
                the_plan = plan.get_plan_for_member_for_gig(a_member, the_gig)
                if the_plan.section == None:
                    need_empty_section = True
                info_block={}
                info_block['the_gig_key'] = the_gig.key
                info_block['the_plan_key'] = the_plan.key
                info_block['the_member_key'] = a_member_key
                info_block['the_band_key'] = the_band_key
                info_block['the_assoc'] = member.get_assoc_for_band_key(the_user, the_band_key)
                print '\n\n{0}'.format(info_block)
                the_plans.append(info_block)
                
            the_section_keys = band.get_section_keys_of_band_key(the_band_key)
            if need_empty_section:
                the_section_keys.append(None)                

            template_args = {
                'title' : 'Gig Info',
                'gig' : the_gig,
                'the_plans' : the_plans,
                'the_section_keys' : the_section_keys
            }
            self.render_template('gig_info.html', template_args)

        else:
            # this is an archived gig
            the_archived_plans = gigarchive.get_archived_plans(the_gig.archive_id)
            template_args = {
                'title' : 'Archived Gig Info',
                'gig' : the_gig,
                'archived_plans' : the_archived_plans,
            }
            self.render_template('gig_archived_info.html', template_args)
            


class EditPage(BaseHandler):
    """ A class for rendering the gig edit page """

    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        if self.request.get("new", None) is not None:
            the_gig = None
            is_new = True
        else:
            the_gig_key = self.request.get("gk", None)
            if (the_gig_key is None):
                return # figure out what to do
                
            the_gig = ndb.Key(urlsafe=the_gig_key).get()
            if the_gig is None:
                self.response.write('did not find a band or gig!')
                return # todo figure out what to do if we didn't find it
            debug_print('found gig object: {0}'.format(the_gig.title))
            is_new = False
                    
        all_bands = member.get_bands_of_member(the_user)
        if not all_bands:
            return # member has no bands, so no point

        template_args = {
            'title' : 'Gig Edit',
            'gig' : the_gig,
            'all_bands' : member.get_bands_of_member(the_user),
            'newgig_is_active' : is_new
        }
        self.render_template('gig_edit.html', template_args)
        
        
    def post(self):
        """post handler - if we are edited by the template, handle it here 
           and redirect back to info page"""


        the_gig_key = self.request.get("gk", '0')
        
        if (the_gig_key == '0'):
            the_gig = None
        else:
            the_gig = ndb.Key(urlsafe=the_gig_key).get()

        # first, get the band
        gig_is_new = False
        gig_band_key = self.request.get("gig_band", None)
        if gig_band_key is not None and gig_band_key != '':
            the_band = ndb.Key(urlsafe=gig_band_key).get()
            if the_gig is None:
                the_gig = new_gig(title="tmp", the_band=the_band)
                gig_is_new = True

        # now get the info
        gig_title = self.request.get("gig_title", None)
        if gig_title is not None and gig_title != '':
            the_gig.title = gig_title
        
        gig_details = self.request.get("gig_details", None)
        if gig_details is not None and gig_details != '':
            the_gig.details = gig_details

        gig_setlist = self.request.get("gig_setlist", None)
        if gig_setlist is not None and gig_setlist != '':
            the_gig.setlist = gig_setlist

        gig_date = self.request.get("gig_date", None)
        if gig_date is not None and gig_date != '':
            the_gig.date = datetime.datetime.strptime(gig_date, \
                                                      '%m/%d/%Y').date()
            # todo validate form entry so date isn't bogus
       
        the_gig.put()            

        if gig_is_new:
            goemail.announce_new_gig(the_gig, self.uri_for('gig_info', _full=True, gk=the_gig.key.urlsafe()))

        return self.redirect(\
            '/gig_info.html?&gk={0}'.format(the_gig.key.urlsafe()))
                
class DeleteHandler(BaseHandler):
    def get(self):

        user = self.user
        
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            the_gig_key = self.request.get("gk", None)

            if the_gig_key is None:
                self.response.write('did not find gig!')
            else:
                the_gig = ndb.Key(urlsafe=the_gig_key).get()
                if the_gig.is_archived:
                    gigarchive.delete_archive(the_gig.archive_id)
                plan.delete_plans_for_gig(the_gig)            
                the_gig.key.delete()
            return self.redirect('/agenda.html')
            
class PrintSetlist(BaseHandler):
    """ print-friendly setlist view """
    
    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        the_gig_key = self.request.get("gk", '0')
        
        if (the_gig_key == '0'):
            return # todo what else to do?
        else:
            the_gig = ndb.Key(urlsafe=the_gig_key).get()

        template_args = {
            'the_gig' : the_gig,
        }
        self.render_template('print_setlist.html', template_args)
        
class ArchiveHandler(BaseHandler):
    """ archive this gig, baby! """
            
    @user_required
    def get(self):

        # find the gig we're interested in
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            self.response.write('no gig key passed in!')
            return # todo figure out what to do if there's no ID passed in
            
        the_gig_key=ndb.Key(urlsafe=gig_key_str)
        if the_gig_key:
            make_archive_for_gig_key(the_gig_key)
            plan_keys = plan.get_plan_keys_for_gig_key(the_gig_key)
            for a_plan_key in plan_keys:
                a_plan_key.delete()

        return self.redirect('/gig_info.html?gk={0}'.format(gig_key_str))
        
