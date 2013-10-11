#
#  member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models
from webapp2_extras.appengine.auth.models import Unique
from webapp2_extras import security

import time

import webapp2
import gig
import band
import plan

from jinja2env import jinja_environment as je

import json
from debug import debug_print

def member_key(member_name='member_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('member', member_name)


class MemberPreferences(ndb.Model):
    """ class to hold user preferences """
    email_new_gig = ndb.BooleanProperty(default=True)

class MemberAssoc(ndb.Model):
    """ class to hold details of the association with a band """
    band = ndb.KeyProperty()
    is_confirmed = ndb.BooleanProperty( default=False )
    is_band_admin = ndb.BooleanProperty( default = False )
    default_section = ndb.KeyProperty( default=None )
    is_multisectional = ndb.BooleanProperty( default = False )
#
# class for member
#
class Member(webapp2_extras.appengine.auth.models.User):
    """ Models a gig-o-matic member """
    name = ndb.StringProperty()
    email_address = ndb.TextProperty()
    phone = ndb.StringProperty(indexed=False)
    statement = ndb.TextProperty()
    is_superuser = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    preferences = ndb.StructuredProperty(MemberPreferences)
    assocs = ndb.StructuredProperty(MemberAssoc, repeated=True)

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
        
def get_all_members():
    """ Return all member objects """
    member_query = Member.query().order(Member.name)
    members = member_query.fetch()
    return members

def get_member_keys_of_band_key(the_band_key):
    """ Return member objects by band"""
    member_query = Member.query( ndb.AND(Member.assocs.band==the_band_key, Member.assocs.is_confirmed==True ) ).order(Member.name)
    members = member_query.fetch(keys_only=True)
    return members

def get_pending_members_from_band_key(the_band_key):
    """ Get all the members who are pending """
    member_query = Member.query( ndb.AND(Member.assocs.band==the_band_key, Member.assocs.is_confirmed==False) ).order(Member.name)
    members = member_query.fetch()
    return members

def get_assoc_for_band_key(the_member, the_band_key):
    """ find the association with a band and return it """
    the_assoc = None
    for a in the_member.assocs:
        if a.band == the_band_key:
            the_assoc=a
            break
    return the_assoc

def get_member_keys_for_band_key_for_section_key(the_band_key, the_section_key):
    """ Return member objects by band with no default section"""
    member_query = Member.query( ndb.AND( Member.assocs.band==the_band_key,
                                          Member.assocs.default_section==the_section_key,
                                          Member.assocs.is_confirmed==True) ).order(Member.name)
    members = member_query.fetch(keys_only=True)
    return members
    
def get_member_keys_of_band_key_no_section(the_band_key):    
    """ Return member objects by band with no default section"""
    member_query = Member.query( ndb.AND( Member.assocs.band==the_band_key, 
                                          Member.assocs.default_section==None,
                                          Member.assocs.is_confirmed==True) ).order(Member.name)
    members = member_query.fetch(keys_only=True)
    return members

def get_associated_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and True if there is one """
    the_status = False
    for a in the_member.assocs:
        if a.band == the_band_key:
            the_status = True
            break
    return the_status

def get_confirmed_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and return the status """
    the_status = False
    for a in the_member.assocs:
        if a.band == the_band_key:
            the_status = a.is_confirmed
            break
    return the_status

def get_admin_status_for_member_for_band_key(the_member, the_band_key):
    """ find the association between this member and a band, and return the status """
    the_status = False
    for a in the_member.assocs:
        if a.band == the_band_key:
            the_status = a.is_band_admin
            break
    return the_status
    
def confirm_member_for_band_key(the_member, the_band_key):
    """ assuming this member is pending, confirm them """
    for i in range(0, len(the_member.assocs)):
        if the_member.assocs[i].band == the_band_key:
            the_member.assocs[i].is_confirmed = True
            the_member.put()
            break

def set_admin_for_member_key_and_band_key(the_member_key, the_band_key, the_do):
    """ find the assoc for this member and band, and make the member an admin (or take it away """
    the_member = the_member_key.get()
    for i in range(0, len(the_member.assocs)):
        if the_member.assocs[i].band == the_band_key:
            the_member.assocs[i].is_band_admin = True if (the_do==1) else False
            the_member.put()
            break
    
def forget_member_from_key(the_member_key):
    """ deletes a member, including all gig plans """

    # first find all of the assocs to bands
    the_assocs=the_member_key.get().assocs
    # delete all plans
    for an_assoc in the_assocs:
        plan.delete_plans_for_member_key_for_band_key(the_member_key, an_assoc.band)

    # delete the old unique values
    the_member=the_member_key.get()
    if the_member:
        Unique.delete_multi(['Member.auth_id:%s'%the_member.email_address,
                             'Member.email_address:%s'%the_member.email_address])  
    # bye!    
    the_member_key.delete()
    
def get_member_from_urlsafe_key(urlsafe):
    """take a urlsafe key and cause an ancestor query to happen, to assure previous writes are committed"""
    untrusted_member=ndb.Key(urlsafe=urlsafe).get()
    return get_member_from_nickname(untrusted_member.nickname)

def get_member_from_key(key):
    """ Return member objects by key"""
    return key.get()

def new_association(member, band):
    """ associate a band and a member """
    assoc=MemberAssoc(band=band.key, is_band_admin=False)
    member.assocs.append(assoc)
    member.put()
    
def delete_association(member, band_key):
    """ delete association between member and band """
    for i in range(0, len(member.assocs)):
        a = member.assocs[i]
        if a.band == band_key:
            member.assocs.pop(i)
            member.put()
            break

def set_default_section(the_member_key, the_band_key, the_section_key):
    """ find the band in a member's list of assocs, and set default section """
    the_member=the_member_key.get()
    print '\n\nsetting default for member {0}'.format(the_member.name)
    if (the_member):
        for i in range(0, len(the_member.assocs)):
            if the_member.assocs[i].band == the_band_key:
                the_member.assocs[i].default_section = the_section_key
                the_member.put()
                break

def set_multi(the_member_key, the_band_key, the_do):
    """ find the band in a member's list of assocs, and set default section """
    the_member=the_member_key.get()
    if (the_member):
        for i in range(0, len(the_member.assocs)):
            if the_member.assocs[i].band == the_band_key:
                the_member.assocs[i].is_multisectional = the_do
                the_member.put()
                break


def get_bands_of_member(the_member):
    """ Return band objects by member"""
    assocs = the_member.assocs
    bands=[a.band.get() for a in assocs]
    return bands

def get_confirmed_bands_of_member(the_member):
    """ Return band objects by member"""
    assocs = the_member.assocs
    bands=[a.band.get() for a in assocs if a.is_confirmed==True]
    return bands

def get_confirmed_assocs_of_member(the_member):
    """ Return assocs objects by member"""
    assocs = the_member.assocs
    the_list=[a for a in assocs if a.is_confirmed==True]
    return the_list

def default_section_for_band_key(the_member, the_band_key):
    """ find the default section for a member within a given band """
    
    the_section = None
    for a in the_member.assocs:
        if a.band == the_band_key:
            the_section = a.default_section
            break
            
    return the_section
        
def member_is_superuser(the_member):
    return the_member.is_superuser

#####
#
# Page Handlers
#
#####

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
                    
        template_args = {
            'title' : 'Member Info',
            'the_member' : the_member,
            'the_bands' : the_bands,
            'all_bands' : band.get_all_bands(),
            'member_is_me' : the_user == the_member
        }
        self.render_template('member_info.html', template_args)


class EditPage(BaseHandler):

    @user_required
    def get(self):
        print 'MEMBER_EDIT GET HANDLER'
        self._make_page(the_user=self.user)

    def _make_page(self, the_user):
        debug_print('IN MEMBER_EDIT {0}'.format(the_user.name))

        the_member_key=self.request.get("mk",'0')
        print 'the_member_key is {0}'.format(the_member_key)
        if the_member_key!='0':
            the_member = ndb.Key(urlsafe=the_member_key).get()
        else:
            the_member = None
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it
        debug_print('found member object: {0}'.format(the_member.name))

        if the_member==None:
            the_cancel_url=self.uri_for("agenda")
        else:
            the_cancel_url=self.uri_for("memberinfo",mk=the_member.key.urlsafe())
#            the_cancel_url="member_info.html?mk={0}".format(the_member.key.urlsafe())

        template_args = {
            'title' : 'Edit Profile',
            'the_member' : the_member,
            'member_is_me' : the_user == the_member,
            'the_cancel_url' : the_cancel_url
        }
        self.render_template('member_edit.html', template_args)
                    

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
       
       # if we're changing email addresses, make sure we're changing to something unique
        member_email=self.request.get("member_email", None)
        if member_email is not None and member_email != '':
            print 'got email {0}'.format(member_email)
            success, existing = \
                Unique.create_multi(['Member.auth_id:%s'%member_email,
                                     'Member.email_address:%s'%member_email])

            if not success:
                self.display_message('Unable to create user for email %s because of \
                    duplicate keys' % member_email)
                return
                
            # delete the old unique values
            Unique.delete_multi(['Member.auth_id:%s'%the_member.email_address,
                                 'Member.email_address:%s'%the_member.email_address])

            the_member.email_address=member_email
            the_member.auth_ids=[member_email]
       
        member_name=self.request.get("member_name", None)
        if member_name is not None and member_name != '':
            print 'got name {0}'.format(member_name)
            the_member.name=member_name
                
        member_phone=self.request.get("member_phone", None)
        if member_phone is not None and member_phone != '':
            print 'got phone {0}'.format(member_phone)
            the_member.phone=member_phone

        member_statement=self.request.get("member_statement", None)
        if member_statement is not None and member_statement != '':
            print 'got statement {0}'.format(member_statement)
            the_member.statement=member_statement

        member_password1=self.request.get("member_password1", None)
        if member_password1 is not None and member_password1 != '':
            member_password2=self.request.get("member_password2", None)
            if member_password2 is not None and member_password2 != '':
                if (member_password1 == member_password2):
                    the_member.set_password(member_password1)
                else:
                    return  # todo figure out what happens if we get this far - should be matched
                            # and validated already on the client side.

        # manage preferences
        if the_member.preferences is None:
            the_member.preferences=MemberPreferences()
            
        member_prefemailnewgig=self.request.get("member_prefemailnewgig", None)
        if (member_prefemailnewgig):
            the_member.preferences.email_new_gig = True
        else:
            the_member.preferences.email_new_gig = False

        the_member.put()                    

        return self.redirect('/member_info.html?mk={0}'.format(the_member.key.urlsafe()))

class ManageBandsGetAssocs(BaseHandler):
    """ returns the assocs related to a member """                   
    def post(self):    
        """ return the bands for a member """
        the_user = self.user

        the_member_key=self.request.get('mk','0')
        
        if the_member_key=='0':
            return # todo figure out what to do
            
        the_member_key=ndb.Key(urlsafe=the_member_key)
        the_member = the_member_key.get()
        
        the_assocs = the_member.assocs

        the_assoc_info=[]
        for an_assoc in the_assocs:
            the_assoc_info.append({
                            'assoc' : an_assoc,
                            'sections' : band.get_section_keys_of_band_key(an_assoc.band)
                            })

        template_args = {
            'the_member' : the_member,
            'the_assoc_info' : the_assoc_info
        }
        self.render_template('member_band_assocs.html', template_args)
        

class ManageBandsNewAssoc(BaseHandler):
    """ makes a new assoc for a member """                   

    def post(self):    
        """ makes a new assoc for a member """
        
        print 'in new assoc handler'
        
        the_user = self.user
        
        the_member_key=self.request.get('mk','0')
        the_band_key=self.request.get('bk','0')
        
        if the_member_key=='0' or the_band_key=='0':
            return # todo figure out what to do
            
        the_member=ndb.Key(urlsafe=the_member_key).get()
        the_band=ndb.Key(urlsafe=the_band_key).get()
        
        new_association(the_member, the_band)
        

class ManageBandsDeleteAssoc(BaseHandler):
    """ deletes an assoc for a member """                   

    def get(self):    
        """ deletes an assoc for a member """
        
        print 'in delete assoc handler'
        
        the_user = self.user
        
        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')

        if the_member_keyurl=='0' or the_band_keyurl=='0':
            return # todo figure out what to do
        
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_band_key=ndb.Key(urlsafe=the_band_keyurl)

        delete_association(the_member_key.get(), the_band_key)
        plan.delete_plans_for_member_key_for_band_key(the_member_key, the_band_key)
        
        return self.redirect('/member_info.html?mk={0}'.format(the_member_keyurl))
        
class SetSection(BaseHandler):
    """ change the default section for a member's band association """
    
    def post(self):
        """ post handler - wants an ak and sk """

        the_section_keyurl=self.request.get('sk','0')
        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')

        if the_section_keyurl=='0' or the_member_keyurl=='0' or the_band_keyurl=='0':
            return # todo figure out what to do

        the_section_key=ndb.Key(urlsafe=the_section_keyurl)
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_band_key=ndb.Key(urlsafe=the_band_keyurl)
        
        set_default_section(the_member_key, the_band_key, the_section_key)

class SetMulti(BaseHandler):
    """ change the default section for a member's band association """
    
    def post(self):
        """ post handler - wants an ak and sk """

        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')
        the_do=self.request.get('do','')

        if the_band_keyurl=='0' or the_member_keyurl=='0':
            return # todo figure out what to do
            
        if  the_do=='':
            return

        the_band_key=ndb.Key(urlsafe=the_band_keyurl)
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        
        set_multi(the_member_key, the_band_key, (the_do=='true'))


class AdminPage(BaseHandler):
    """ Page for member administration """

    @user_required
    def get(self):
        if member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return;
            
    def _make_page(self,the_user):
    
        # todo make sure the user is a superuser
        
        the_members = get_all_members()
        
        print '\n\n{0}\n\n'.format([x.name for x in the_members])
        
        template_args = {
            'title' : 'Member Admin',
            'the_members' : the_members,
        }
        self.render_template('member_admin.html', template_args)

class DeleteMember(BaseHandler):
    """ completely delete member """
    
    @user_required
    def get(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')

        if the_member_keyurl=='0':
            return # todo figure out what to do

        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        
        the_user = self.user # todo - make sure the user is a superuser
        
        if (the_user != the_member_key):
            forget_member_from_key(the_member_key)
        else:
            print 'cannot delete yourself, people'

        return self.redirect('/member_admin.html')
        
class AdminMember(BaseHandler):
    """ grant or revoke admin rights """
    
    @user_required
    def get(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        the_do=self.request.get('do','')

        if the_member_keyurl=='0':
            return # todo figure out what to do

        if the_do=='':
            return # todo figure out what to do

        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_member=the_member_key.get()
        
        # todo - make sure the user is a superuser
        if (the_do=='0'):
            the_member.is_superuser=False
        elif (the_do=='1'):
            the_member.is_superuser=True
        else:
            return # todo figure out what to do

        the_member.put()

        return self.redirect('/member_admin.html')        