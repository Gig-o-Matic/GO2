#
# member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import time

import webapp2
import member
import assoc
import gig
import band
from jinja2env import jinja_environment as je

from debug import debug_print

def member_key(member_name='member_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('member', member_name)

#
# class for member
#
class Member(webapp2_extras.appengine.auth.models.User):

    """ Models a gig-o-matic member """
    name = ndb.StringProperty()
    email_address = ndb.TextProperty()
    phone = ndb.StringProperty(indexed=False)
    statement = ndb.TextProperty()
    role = ndb.IntegerProperty(default=0) # 0=vanilla member, 1=admin
    created = ndb.DateTimeProperty(auto_now_add=True)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
                The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)

    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
                The user_id of the requesting user.
        :param token:
                The token string to be verified.
        :returns:
                A tuple ``(User, timestamp)``, with a user object and
                the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
                timestamp = int(time.mktime(valid_token.created.timetuple()))
                return user, timestamp

        return None, None
    
def get_member_from_urlsafe_key(urlsafe):
    """take a urlsafe key and cause an ancestor query to happen, to assure previous writes are committed"""
    untrusted_member=ndb.Key(urlsafe=urlsafe).get()
    return get_member_from_nickname(untrusted_member.nickname)

def get_member_from_key(key):
    """ Return member objects by key"""
    return key.get()

def get_member_from_id(id):
    """ Return member object by id"""
    debug_print('get_member_from_id looking for id {0}'.format(id))
    return Member.get_by_id(int(id), parent=member_key()) # todo more efficient if we use the band because it's the parent?

def get_bands_of_member(the_member):
    """ Return band objects by member"""
    assoc_query = assoc.Assoc.query(assoc.Assoc.member==the_member.key, ancestor=assoc.assoc_key())
    assocs = assoc_query.fetch()
    debug_print('get_bands_of_member: got {0} assocs for member key id {1} ({2})'.format(len(assocs),the_member.key.id(),the_member.name))
    bands=[a.band.get() for a in assocs]
    debug_print('get_bands_of_member: found {0} bands for member {1}'.format(len(bands),the_member.name))
    return bands
    
def get_current_band(the_member):
    """return member's band; assume every member has just one band, for now"""
    bands=get_bands_of_member(the_member)
    if len(bands)>0:
        return bands[0]
    else:
        return None

def nav_info(the_user, the_member):

        if (the_member is not None):
            if the_user.key == the_member.key:
                is_me=True
            else:
                is_me=False
        else:
            is_me=False
            
        if member_is_admin(the_user):
            is_admin=True
        else:
            is_admin=False
                        
        return { 'the_user': the_user,
                 'is_me': is_me,
                 'is_admin': is_admin
        }
        
def member_is_admin(the_member):
    return the_member.role==1

class InfoPage(BaseHandler):
    """Page for showing information about a member"""

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        print 'IN MEMBER_INFO {0}'.format(the_user.name)

        the_member_key=self.request.get("mk",'0')
        print 'member_key is {0}'.format(the_member_key)
        if the_member_key!='0':
            # if we've just edited this member, the database may not have
            # invalidated the cache. Therefore, use a method to get the 
            # member that uses an ancestor query.
#            the_member=member.get_member_from_urlsafe_key(the_member_key)
            the_member=ndb.Key(urlsafe=the_member_key).get()
        else:
            return # todo what to do if it's not passed in?
            
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it
        debug_print('found member object: {0}'.format(the_member.name))
        
        if the_member.key == the_user.key:
            is_me = True
        else:
            is_me = False
            
        # find the bands this member is associated with
        the_bands=get_bands_of_member(the_member)
        
        if the_bands is None:
            return # todo figure out what to do if there are no bands for this member
                    
        template = je.get_template('member_info.html')
        self.response.write( template.render(
            title='Member Info',
            the_user=the_user,
            the_member=the_member,
            the_bands=the_bands,
            nav_info=member.nav_info(the_user, the_member)
        ) )


class EditPage(BaseHandler):

    @user_required
    def get(self):
        print 'MEMBER_EDIT GET HANDLER'
        self._make_page(the_user=self.user)

    def _make_page(self, the_user):
        debug_print('IN MEMBER_EDIT {0}'.format(the_user.name))

        if self.request.get("new", None) is not None:
            #  creating a new member
             the_member=None
             is_new=True
        else:
            is_new=False
            the_member_key=self.request.get("mk",'0')
            print 'the_member_key is {0}'.format(the_member_key)
            if the_member_key!='0':
                the_member=ndb.Key(urlsafe=the_member_key).get()
            else:
                the_member=the_user
            if the_member is None:
                self.response.write('did not find a member!')
                return # todo figure out what to do if we didn't find it
            debug_print('found gig object: {0}'.format(the_member.name))
                    
        template = je.get_template('member_edit.html')
        self.response.write( template.render(
            title='Edit Profile',
            the_member=the_member,
            the_bands=band.get_all_bands(),
            nav_info=member.nav_info(the_user, the_member),
            newmember_is_active=is_new
        ) )        

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'MEMBER_EDIT POST HANDLER'

        print str(self.request.arguments())

        the_user = self.user            

        the_member_key=self.request.get("mk",'0')
        
        if the_member_key=='0':
            # it's a new user
            the_member=new_member()
        else:
            the_member=ndb.Key(urlsafe=the_member_key).get()
            
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it
       
        member_name=self.request.get("member_name", None)
        if member_name is not None and member_name != '':
            print 'got name {0}'.format(member_name)
            the_member.name=member_name
                
        member_email=self.request.get("member_email", None)
        if member_email is not None and member_email != '':
            print 'got email {0}'.format(member_email)
            the_member.email_address=member_email

        member_phone=self.request.get("member_phone", None)
        if member_phone is not None and member_phone != '':
            print 'got phone {0}'.format(member_phone)
            the_member.phone=member_phone

        member_statement=self.request.get("member_statement", None)
        if member_statement is not None and member_statement != '':
            print 'got statement {0}'.format(member_statement)
            the_member.statement=member_statement

        the_member.put()            
        
        member_addband = self.request.get('member_addband', None)
        if member_addband is not None and member_addband != '':
            print 'got addband {0}'.format(member_addband)
            the_band=band.get_band_from_name(member_addband)
            if the_band is not None:
                assoc.new_association(the_band, the_member)
            else:
                print 'didn\'t find a band!'
        

        return self.redirect('/member_info.html?mk={0}'.format(the_member.key.urlsafe()))
