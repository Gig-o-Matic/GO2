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
import gigcomment
import assoc
import jinja2env

from debug import debug_print
import datetime

#
# class for gig
#
class Gig(ndb.Model):
    """ Models a gig-o-matic gig """
    title = ndb.StringProperty()
    contact = ndb.KeyProperty()
    details = ndb.TextProperty()
    setlist = ndb.TextProperty()
    date = ndb.DateProperty(auto_now_add=True)
    call = ndb.TextProperty( default=None )
    status = ndb.IntegerProperty( default=0 )
    archive_id = ndb.TextProperty()
    is_archived = ndb.ComputedProperty(lambda self: self.archive_id is not None)
    comment_id = ndb.TextProperty( default = None)
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
        
def adjust_date_for_band(the_band, the_date):
    if the_band.time_zone_correction:
        # this band is in a non-UTC time zone!
        the_date=the_date+datetime.timedelta(hours=the_band.time_zone_correction)
    the_date = the_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return the_date
    
def get_gigs_for_bands(the_band_list, num=None, start_date=None, keys_only=False):
    """ Return gig objects by band, ignoring past gigs """
        
    if (type(the_band_list) is not list):
        the_band_list = [the_band_list]

    if start_date:
        start_date = adjust_date_for_band(the_band_list[0], start_date)
    
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
    
    
    
def get_gigs_for_band_key_for_dates(the_band_key, start_date, end_date):
    """ Return gig objects by band, past gigs OK """

    if start_date:
        start_date = adjust_date_for_band(the_band_key.get(), start_date)

    if end_date:
        end_date = adjust_date_for_band(the_band_key.get(), end_date)

    gig_query = Gig.query(ndb.AND(Gig.date >= start_date, \
                                  Gig.date <= end_date), \
                                  ancestor=the_band_key).order(Gig.date)
    gigs = gig_query.fetch()
    return gigs

def get_gigs_for_member_for_dates(the_member, start_date, end_date):
    """ return gig objects for the bands of a member """
    the_bands = assoc.get_confirmed_bands_of_member(the_member)

    if start_date:
        start_date = adjust_date_for_band(the_bands[0], start_date)

    if end_date:
        end_date = adjust_date_for_band(the_bands[0], end_date)

    all_gigs = []
    for a_band in the_bands:
        all_gigs.extend(get_gigs_for_band_key_for_dates(a_band.key, \
                                                    start_date, \
                                                    end_date))
    return all_gigs

def get_old_gig_keys(end_date):
    """ Return gig objects by band, past gigs OK """
    
    # todo do we need to adjust the date?
    
    gig_query = Gig.query(ndb.AND(Gig.is_archived == False, \
                                  Gig.date <= end_date))
    gigs = gig_query.fetch(keys_only=True)
    return gigs
    
def set_sections_for_empty_plans(the_gig):
    """ For this gig, get all plans. For plans with no section set, get the users default and set it """
    """ This is used when freezing a gig's plans """
    
    the_plan_keys = plan.get_plan_keys_for_gig_key(the_gig.key)
    the_band_key = the_gig.key.parent()
    for a_plan_key in the_plan_keys:
        a_plan = a_plan_key.get()
        if a_plan.section is None:
            the_member_key = a_plan.member
            the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
            if the_assoc:
                a_plan.section = the_assoc.default_section
                a_plan.put()
            
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

        # also delete any plans, since they're all now in the archive
        plan_keys = plan.get_plan_keys_for_gig_key(the_gig_key)
        for a_plan_key in plan_keys:
            a_plan_key.delete()


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

        the_comment_text = None
        if the_gig.comment_id:
            the_comment_text = gigcomment.get_comment(the_gig.comment_id)
            
        if not the_gig.is_archived:
            the_band_key = the_gig.key.parent()

            the_assocs = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=True, keys_only=False)

            the_plans = []
        
            need_empty_section = False
            for the_assoc in the_assocs:
                a_member_key = the_assoc.member
                a_member = a_member_key.get()
                the_plan = plan.get_plan_for_member_for_gig(a_member, the_gig)
                if the_plan.section==None and the_assoc.default_section==None:
                    need_empty_section = True
                info_block={}
                info_block['the_gig_key'] = the_gig.key
                info_block['the_plan_key'] = the_plan.key
                info_block['the_member_key'] = a_member_key
                info_block['the_band_key'] = the_band_key
                info_block['the_assoc'] = the_assoc
                if the_plan.section is not None:
                    info_block['the_section'] = the_plan.section
                else:
                    info_block['the_section'] = the_assoc.default_section            
                the_plans.append(info_block)          
        
            the_section_keys = band.get_section_keys_of_band_key(the_band_key)
            if need_empty_section:
                the_section_keys.append(None)


            template_args = {
                'title' : 'Gig Info',
                'gig' : the_gig,
                'the_plans' : the_plans,
                'the_section_keys' : the_section_keys,
                'comment_text' : the_comment_text
            }
            self.render_template('gig_info.html', template_args)

        else:
            # this is an archived gig
            the_archived_plans = gigarchive.get_archived_plans(the_gig.archive_id)
            template_args = {
                'title' : 'Archived Gig Info',
                'gig' : the_gig,
                'archived_plans' : the_archived_plans,
                'comment_text' : the_comment_text
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
            is_new = False

        if is_new:
            user_is_band_admin = False
        else:
            user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(the_user, the_gig.key.parent())
            
        all_bands = assoc.get_confirmed_bands_of_member(the_user)
        if not all_bands:
            template_args = {
                'title' : 'Add a Gig',
            }
            self.render_template('no_band_gig.html', template_args)
        else:
            template_args = {
                'title' : 'Gig Edit',
                'gig' : the_gig,
                'all_bands' : all_bands,
                'user_is_band_admin': user_is_band_admin,
                'newgig_is_active' : is_new
            }
            self.render_template('gig_edit.html', template_args)
        
    @user_required        
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
        
        gig_contact = self.request.get("gig_contact", None)
        if gig_contact is not None and gig_contact != '':
            the_gig.contact = ndb.Key(urlsafe=gig_contact)
        
        gig_details = self.request.get("gig_details", None)
        if gig_details is not None:
            the_gig.details = gig_details

        gig_setlist = self.request.get("gig_setlist", None)
        if gig_setlist is not None:
            the_gig.setlist = gig_setlist

        gig_date = self.request.get("gig_date", None)
        if gig_date is not None and gig_date != '':
            the_gig.date = datetime.datetime.strptime(gig_date, \
                                                      '%m/%d/%Y').date()
            # todo validate form entry so date isn't bogus
       
        gig_call = self.request.get("gig_call", '')
        if gig_call is not None:
            the_gig.call = gig_call

        gig_status = self.request.get("gig_status", '0')
        the_gig.status = int(gig_status)

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
                if the_gig.comment_id:
                    gigcomment.delete_comment(the_gig.comment_id)
                plan.delete_plans_for_gig(the_gig)            
                the_gig.key.delete()
            return self.redirect('/agenda.html')
            
class PrintSetlist(BaseHandler):
    """ print-friendly setlist view """
    
    @user_required
    def get(self):
        self._make_page(self.user)

    def _make_page(self, the_user):

        the_gig_keyurl = self.request.get("gk", '0')
        
        if (the_gig_keyurl == '0'):
            return # todo what else to do?
        else:
            the_gig = ndb.Key(urlsafe=the_gig_keyurl).get()

        template_args = {
            'the_gig' : the_gig,
        }
        self.render_template('print_setlist.html', template_args)
        
class PrintPlanlist(BaseHandler):
    """ print-friendly list of member plans """
    
    @user_required
    def get(self):
        self._make_page(self.user)
    
    def _make_page(self, the_user):
        the_gig_keyurl = self.request.get("gk", '0')
        
        if (the_gig_keyurl == '0'):
            return # todo what else to do?
        else:
            the_gig_key = ndb.Key(urlsafe=the_gig_keyurl)
            
        the_gig = the_gig_key.get()   
        the_band_key = the_gig_key.parent()
        the_member_keys = assoc.get_member_keys_of_band_key(the_band_key)
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
            info_block['the_assoc'] = assoc.get_assoc_for_band_key_and_member_key(the_user.key, the_band_key)
            the_plans.append(info_block)
            
        the_section_keys = band.get_section_keys_of_band_key(the_band_key)
        if need_empty_section:
            the_section_keys.append(None)                

        template_args = {
            'title' : 'Gig Info',
            'the_gig' : the_gig,
            'the_plans' : the_plans,
            'the_section_keys' : the_section_keys
        }
        self.render_template('print_planlist.html', template_args)
        
            
        
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

        return self.redirect('/gig_info.html?gk={0}'.format(gig_key_str))
        
class AutoArchiveHandler(BaseHandler):
    """ automatically archive old gigs """
    def get(self):
        date = datetime.datetime.now()
        end_date = date - datetime.timedelta(days=3)
        the_gig_keys = get_old_gig_keys(end_date = end_date)
        for a_gig_key in the_gig_keys:
            make_archive_for_gig_key(a_gig_key)
        goemail.notify_superuser_of_archive(len(the_gig_keys))
        
class CommentHandler(BaseHandler):
    """ takes a new comment and adds it to the gig """

    @user_required
    def post(self):
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in

        the_gig_key = ndb.Key(urlsafe=gig_key_str)
        the_gig = the_gig_key.get()

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str=='':
            return
        
        dt=datetime.datetime.now()

        offset_str = self.request.get("o", None)
        if comment_str is not None:
            offset=int(offset_str)
            dt = dt - datetime.timedelta(hours=offset)

        user=self.user
        timestr=dt.strftime('%-m/%-d/%Y %I:%M%p')
        new_comment = '{0} ({1}) said at {2}:\n{3}'.format(user.name, user.email_address, timestr, comment_str)

        new_id, the_comment_text = gigcomment.add_comment_for_gig(new_comment, the_gig.comment_id)
        if new_id != the_gig.comment_id:
            the_gig.comment_id = new_id
            the_gig.put()

        self.response.write(jinja2env.html_content(the_comment_text))

class GetCommentHandler(BaseHandler):
    """ returns the comment for a gig if there is one """
    
    @user_required
    def post(self):
    
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig = ndb.Key(urlsafe=gig_key_str).get()

        if the_gig.comment_id:
            the_comment = gigcomment.get_comment(the_gig.comment_id)
            
            self.response.write(jinja2env.html_content(the_comment))
        else:
            self.response.write('')
