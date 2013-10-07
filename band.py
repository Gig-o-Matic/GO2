#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
from jinja2env import jinja_environment as je
from debug import *

import assoc
import member
import goemail

def band_key(band_name='band_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Band', band_name)

#
# class for band
#
class Band(ndb.Model):
    """ Models a gig-o-matic band """
    name = ndb.StringProperty()
    website = ndb.TextProperty()
    description = ndb.TextProperty()
    sections = ndb.KeyProperty( repeated=True ) # instrumental sections
    created = ndb.DateTimeProperty(auto_now_add=True)
    time_zone_correction = ndb.IntegerProperty(default=0)

def new_band(name):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name)
    the_band.put()
    debug_print('new_band: added new band: {0}'.format(name))
    return the_band
        
def get_band_from_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.query(Band.name==band_name, ancestor=band_key())
    band = bands_query.fetch(1)
    debug_print('get_band_from_name: found {0} bands for name {1}'.format(len(band),band_name))
    if len(band)==1:
        return band[0]
    else:
        return None
        
def get_band_from_key(key):
    """ Return band objects by key"""
    return key.get()

def get_band_from_id(id):
    """ Return band object by id"""
    debug_print('get_band_from_id looking for id {0}'.format(id))
    return Band.get_by_id(int(id), parent=band_key()) # todo more efficient if we use the band because it's the parent?
    
def get_member_keys_of_band_key(the_band_key):
    """ Return member objects by band"""
    assoc_query = assoc.Assoc.query(assoc.Assoc.band==the_band_key, ancestor=assoc.assoc_key())
    assocs = assoc_query.fetch()
    members=[a.member for a in assocs]
    return members

def get_all_bands():
    """ Return all objects"""
    bands_query = Band.query(ancestor=band_key())
    all_bands = bands_query.fetch()
    debug_print('get_all_bands: found {0} bands'.format(len(all_bands)))
    return all_bands

def get_section_keys_of_band_key(the_band_key):
    return the_band_key.get().sections

def get_member_keys_of_band_key_by_section_key(the_band_key):
    the_info=[]
    section_keys=get_section_keys_of_band_key(the_band_key)
    for a_section_key in section_keys:
        the_member_keys=assoc.get_member_keys_for_section_key(a_section_key)
        the_info.append([a_section_key,the_member_keys])

    no_section_members=assoc.get_member_keys_of_band_key_no_section(the_band_key)
    if no_section_members:
        the_info.append([None,no_section_members])

    return the_info

def get_pending_members_from_band_key(the_band_key):
    """ Get all the members who have a status of 0 """
    assoc_query = assoc.Assoc.query(assoc.Assoc.band==the_band_key, assoc.Assoc.status==0, ancestor=assoc.assoc_key())
    assocs = assoc_query.fetch()
    members=ndb.get_multi([a.member for a in assocs])
    return members
    
def new_section_for_band(the_band, the_section_name):
    the_section = Section(parent=the_band.key, name=the_section_name)
    the_section.put()
    debug_print('new section {0} for band {1}'.format(the_section_name, the_band.name))
    if the_band.sections:
        if the_section not in the_band.sections:
            the_band.sections.append(the_section.key)
    else:
        the_band.sections=[the_section.key]
    the_band.put()
    return the_section

def delete_section_key(the_section_key):
    #todo make sure the section is empty before deleting it

    # get the parent band's list of sections and delete ourselves
    the_band=the_section_key.parent().get()
    if the_section_key in the_band.sections:
        i=the_band.sections.index(the_section_key)
        the_band.sections.pop(i)
        the_band.put()
    the_section_key.delete()

#
# class for section
#
class Section(ndb.Model):
    """ Models an instrument section in a band """
    name = ndb.StringProperty()

#
#
# Handlers
#
#

class InfoPage(BaseHandler):
    """ class to produce the band info page """

    @user_required
    def get(self):    
        """ make the band info page """
        self._make_page(the_user=self.user)

    def _make_page(self,the_user):
        """ produce the info page """
        
        # find the band we're interested in
        band_key_str=self.request.get("bk", None)
        if band_key_str is None:
            self.response.write('no band key passed in!')
            return # todo figure out what to do if there's no ID passed in

        the_band_key=ndb.Key(urlsafe=band_key_str)
        the_band=the_band_key.get()

        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
            
        the_assoc=assoc.get_assoc_for_band_key_and_member_key(the_band_key, the_user.key)
        if the_assoc:
            the_user_status=the_assoc.status
        else:
            the_user_status=-1 # no relationship to the band

        if the_user_status==2 or member.member_is_superuser(the_user):
            the_pending = get_pending_members_from_band_key(the_band_key)
        else:
            the_pending = []

        template_args = {
            'title' : 'Band Info',
            'the_band' : the_band,
            'the_user_status' : the_user_status,
            'the_pending_members' : the_pending,
            'nav_info' : member.nav_info(the_user, None)
        }
        self.render_template('band_info.html', template_args)

        # todo make sure the admin is really there
        
class EditPage(BaseHandler):

    @user_required
    def get(self):
        print 'BAND_EDIT GET HANDLER'
        self.make_page(the_user=self.user)

    def make_page(self, the_user):
        debug_print('IN BAND_EDIT {0}'.format(the_user.name))

        if self.request.get("new",None) is not None:
            #  creating a new band
            # todo MAKE SURE I'M AN ADMIN
            the_band=None
            is_new=True
        else:
            is_new=False
            the_band_key=self.request.get("bk",'0')
            print 'the_band_key is {0}'.format(the_band_key)
            if the_band_key=='0':
                return
            else:
                the_band=ndb.Key(urlsafe=the_band_key).get()
                if the_band is None:
                    self.response.write('did not find a band!')
                    return # todo figure out what to do if we didn't find it
                debug_print('found band object: {0}'.format(the_band.name))

        template_args = {
            'title' : 'Band Edit',
            'the_band' : the_band,
            'nav_info' : member.nav_info(the_user, None),
            'newmember_is_active' : is_new,
            'is_new' : is_new
        }
        self.render_template('band_edit.html', template_args)
                    
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'BAND_EDIT POST HANDLER'

        print str(self.request.arguments())

        the_user = self.user

        the_band_key=self.request.get("bk",'0')
        
        if the_band_key=='0':
            # it's a new band
            the_band=new_band('tmp')
        else:
            the_band=ndb.Key(urlsafe=the_band_key).get()
            
        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
       
        band_name=self.request.get("band_name",None)
        if band_name is not None and band_name != '':
            print 'got name {0}'.format(band_name)
            the_band.name=band_name
                
        band_website=self.request.get("band_website",None)
        if band_website is not None and band_website != '':
            print 'got website {0}'.format(band_website)
            the_band.website=band_website

        band_description=self.request.get("band_description",None)
        if band_description is not None and band_description != '':
            print 'got description {0}'.format(band_description)
            the_band.description=band_description
            
        band_tz=self.request.get("band_tz",None)
        if band_tz is not None and band_tz != '':
            print 'got tz {0}'.format(band_tz)
            the_band.time_zone_correction=int(band_tz)

        the_band.put()            

        return self.redirect('/band_info.html?bk={0}'.format(the_band.key.urlsafe()))
        
class BandGetMembers(BaseHandler):
    """ returns the members related to a band """                   

    def post(self):    
        """ return the members for a band """
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do
            
        the_band_key = ndb.Key(urlsafe=the_band_key_str)
        the_assocs = assoc.get_assocs_of_band_key(the_band_key)

        the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_band_key, the_user.key)
        the_user_status=-1
        if the_assoc:
            the_user_status = the_assoc.status       
        
        template_args = {
            'the_assocs' : the_assocs,
            'the_user_status' : the_user_status,
            'nav_info' : member.nav_info(the_user, None)    
        }
        self.render_template('band_members.html', template_args)

class BandGetSections(BaseHandler):
    """ returns the sections related to a band """                   

    def post(self):    
        """ return the sections for a band """
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do
            
        the_band_key = ndb.Key(urlsafe=the_band_key_str)
        the_members_by_section = get_member_keys_of_band_key_by_section_key(the_band_key)

        the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_band_key, the_user.key)
        the_user_status=-1
        if the_assoc:
            the_user_status = the_assoc.status       
                
        template_args = {
            'the_members_by_section' : the_members_by_section,
            'nav_info' : member.nav_info(the_user, None),
            'the_user_status' : the_user_status
        }
        self.render_template('band_sections.html', template_args)

class NewSection(BaseHandler):
    """ makes a new section for a band """                   

    def post(self):    
        """ makes a new assoc for a member """
        
        print 'in new section handler'
        
        the_user = self.user
        
        the_section_name=self.request.get('section_name','0')
        the_band_key=self.request.get('bk','0')
        
        if the_section_name=='0' or the_band_key=='0':
            return # todo figure out what to do
            
        the_band=ndb.Key(urlsafe=the_band_key).get()
        
        new_section_for_band(the_band, the_section_name)

class DeleteSection(BaseHandler):
    """ makes a new section for a band """                   

    def post(self):    
        """ makes a new assoc for a member """
        
        print 'in new section handler'
        
        the_user = self.user
        
        the_section_key_url=self.request.get('sk','0')
        
        if the_section_key_url=='0':
            return # todo figure out what to do

        the_section_key=ndb.Key(urlsafe=the_section_key_url)
        
        delete_section_key(the_section_key)

class MoveSection(BaseHandler):
    """ move a section for a band """                   

    @user_required
    def post(self):    
        """ moves a section """
        
        the_user = self.user
        
        the_direction=self.request.get('dir','0')
        the_section_key=self.request.get('sk','0')
        
        the_section_key=ndb.Key(urlsafe=the_section_key)
        the_section=the_section_key.get()
        the_band=the_section_key.parent().get()
        
        band_sections = the_band.sections
        if the_section_key in band_sections:
            i = band_sections.index(the_section_key)
            band_sections.pop(i)
            if the_direction == '1':
                band_sections.insert(i-1, the_section_key)
            else:
                band_sections.insert(i+1, the_section_key)
        
            the_band.sections=band_sections
            the_band.put()
        else:
            print 'not in band'
        
class ConfirmMember(BaseHandler):
    """ move a member from pending to 'real' member """
    
    @user_required
    def get(self):
        """ handles the 'confirm member' button in the band info page """
        
        the_user = self.user

        # todo make sure we are a band admin        
        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')
        
        if the_member_keyurl=='0' or the_band_keyurl=='0':
            return # todo what to do?
            
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_band_key=ndb.Key(urlsafe=the_band_keyurl)
                    
        the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_band_key, the_member_key)
        
        if the_assoc is None:
            return # todo what to do?
            
        the_assoc.status=1
        the_assoc.put()

        the_member = the_member_key.get()
        the_band = the_band_key.get()
        goemail.send_band_accepted_email(the_member.email_address, the_band.name)

        return self.redirect('/band_info.html?bk={0}'.format(the_band_keyurl))
        
class AdminMember(BaseHandler):
    """ grant or revoke admin rights """
    
    @user_required
    def get(self):
        """ post handler - wants an ak """
        
        # todo - make sure the user is a superuser or already an admin of this band

        the_assoc_keyurl=self.request.get('ak','0')
        the_do=self.request.get('do','')

        if the_assoc_keyurl=='0':
            return # todo figure out what to do

        if the_do=='':
            return # todo figure out what to do

        the_assoc=ndb.Key(urlsafe=the_assoc_keyurl).get()

        print 'found assoc: {0}'.format(the_assoc)
        if the_assoc:
            if (the_do == '0'):
                the_assoc.status=1
            elif (the_do == '1'):
                the_assoc.status=2
            the_assoc.put()
        else:
            return # todo figure out what to do

        return self.redirect('/band_info.html?bk={0}'.format(the_assoc.band.urlsafe()))

class RemoveMember(BaseHandler):
    """ grant or revoke admin rights """
    
    @user_required
    def get(self):
        """ post handler - wants an ak """
        
        # todo - make sure the user is a superuser or already an admin of this band

        the_assoc_keyurl=self.request.get('ak','0')

        if the_assoc_keyurl=='0':
            return # todo figure out what to do

        the_assoc=ndb.Key(urlsafe=the_assoc_keyurl).get()

        if the_assoc:
            the_assoc.key.delete()
        else:
            return # todo figure out what to do

        return self.redirect('/band_info.html?bk={0}'.format(the_assoc.band.urlsafe()))

class AdminPage(BaseHandler):
    """ Page for band administration """

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
    
        # todo make sure the user is a superuser
        
        the_bands = get_all_bands()
        
        template_args = {
            'title' : 'Band Admin',
            'the_bands' : the_bands,
            'nav_info' : member.nav_info(the_user)
        }
        self.render_template('band_admin.html', template_args)
