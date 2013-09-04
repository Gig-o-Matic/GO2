#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#
from google.appengine.api import users
from google.appengine.ext import ndb
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
    created = ndb.DateTimeProperty(auto_now_add=True)

def new_band(name, admin):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name, adminkey=admin.key)
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
    
def get_members_of_band(the_band):
    """ Return member objects by band"""
    assoc_query = assoc.Assoc.query(assoc.Assoc.band==the_band.key, ancestor=assoc.assoc_key())
    assocs = assoc_query.fetch()
    debug_print('get_members_of_band: got {0} assocs for band key id {1} ({2})'.format(len(assocs),the_band.key.id(),the_band.name))
    members=[a.member.get() for a in assocs]
    debug_print('get_members_of_band: found {0} members for band {1}'.format(len(members),the_band.name))
    return members

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
        debug_print('IN BAND_INFO {0}'.format(user.nickname()))

        the_user=member.get_member_from_nickname(user.nickname())

        # find the band we're interested in
        band_key_str=self.request.get("bk", None)
        if band_key_str is None:
            self.response.write('no band key passed in!')
            return # todo figure out what to do if there's no ID passed in

        band_key=ndb.Key(urlsafe=band_key_str)
        the_band=band_key.get()

        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
            
        debug_print('found band object: {0}'.format(the_band.name))

        the_members=get_members_of_band(the_band)
                    
        template = je.get_template('band_info.html')
        self.response.write( template.render(
            title='Band Info',
            the_user=the_user,
            the_band=the_band,
            the_admin=the_band.adminkey.get(),
            the_members=the_members,
            nav_info=member.nav_info(the_user, None)
        ) )
        # todo make sure the admin is really there
        
class EditPage(webapp2.RequestHandler):
    def get(self):
        print 'BAND_EDIT GET HANDLER'
        the_user = users.get_current_user()
        if the_user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(the_user)

    def make_page(self, user):
        debug_print('IN BAND_EDIT {0}'.format(user.nickname()))

        the_user=member.get_member_from_nickname(user.nickname())
                
        if the_user is None:
            return # todo figure out what to do if we get this far and there's no member

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
                    
        template = je.get_template('band_edit.html')
        self.response.write( template.render(
            title='Band Edit',
            the_user=the_user,
            the_band=the_band,
            nav_info=member.nav_info(the_user, None),
            newmember_is_active=is_new
        ) )        

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'BAND_EDIT POST HANDLER'

        print str(self.request.arguments())

        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return;

        the_band_key=self.request.get("bk",'0')
        
        if the_band_key=='0':
            # it's a new band
            the_band=new_band('tmp',user)
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
        

