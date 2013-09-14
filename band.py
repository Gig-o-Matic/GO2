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

def band_key(band_name='band_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Band', band_name)

#
# class for band
#
class Band(ndb.Model):
    """ Models a gig-o-matic band """
    name = ndb.StringProperty()
    adminkey = ndb.KeyProperty()
    website = ndb.TextProperty()
    description = ndb.TextProperty()
    sections = ndb.KeyProperty( repeated=True ) # instrumental sections
    created = ndb.DateTimeProperty(auto_now_add=True)

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
#     sections_query = Section.query(ancestor=the_band_key)
#     all_sections = sections_query.fetch(keys_only=True)
#     debug_print('get_sections_of_band: found {0} sections for band {1}'.format(len(all_sections), the_band_key.get().name))
#     return all_sections

def get_member_keys_of_band_key_by_section_key(the_band_key):
    the_info=[]
    section_keys=get_section_keys_of_band_key(the_band_key)
    for a_section_key in section_keys:
        the_member_keys=assoc.get_member_keys_for_section_key(a_section_key)
        the_info.append([a_section_key,the_member_keys])
    return the_info
    
    
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

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)

    def _make_page(self,the_user):
        debug_print('IN BAND_INFO {0}'.format(the_user.name))

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
            
        if the_band.adminkey:
            the_admin=the_band.adminkey.get()
        else:
            the_admin=None

        debug_print('found band object: {0}'.format(the_band.name))

        template_args = {
            'title' : 'Band Info',
            'the_band' : the_band,
            'the_admin' : the_admin,
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
        the_members_by_section = get_member_keys_of_band_key_by_section_key(the_band_key)
                
        template_args = {
            'the_members_by_section' : the_members_by_section,
            'nav_info' : member.nav_info(the_user, None)            
        }
        self.render_template('band_members.html', template_args)

class BandGetSections(BaseHandler):
    """ returns the sections related to a band """                   

    def post(self):    
        """ return the sections for a band """
        the_user = self.user

        the_band_key=self.request.get('bk',0)
        
        if the_band_key==0:
            return # todo figure out what to do
            
        the_band = ndb.Key(urlsafe=the_band_key).get()
        
        the_sections = the_band.sections
        if not the_sections:
            the_sections=[]
        
        print 'got {0} sections for band {1}'.format(len(the_sections), the_band.name)
        
        
        template_args = {
            'the_sections' : the_sections,
            'nav_info' : member.nav_info(the_user, None)
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

class MoveSection(BaseHandler):
    """ move a section for a band """                   

    def post(self):    
        """ moves a section """
        
        print 'in new section move handler'
        
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
        
            