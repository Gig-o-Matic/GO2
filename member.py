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
import goemail
import assoc
import login
import datetime
import lang

import logging
from babel.dates import format_date, format_datetime, format_time

import json
from debug import debug_print

def member_key(member_name='member_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('member', member_name)

class MemberPreferences(ndb.Model):
    """ class to hold user preferences """
    email_new_gig = ndb.BooleanProperty(default=True)
    hide_canceled_gigs = ndb.BooleanProperty(default=False)
    locale = ndb.TextProperty(default='en')
    share_profile = ndb.BooleanProperty(default=True)
    share_email = ndb.BooleanProperty(default=False)

#
# class for member
#
class Member(webapp2_extras.appengine.auth.models.User):
    """ Models a gig-o-matic member """
    name = ndb.StringProperty()
    lower_name = ndb.ComputedProperty(lambda self: self.name.lower())    
    nickname = ndb.StringProperty( default=None )
    email_address = ndb.TextProperty()
    phone = ndb.StringProperty(default='', indexed=False)
    statement = ndb.TextProperty(default='')
    is_superuser = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    preferences = ndb.StructuredProperty(MemberPreferences)
    seen_motd = ndb.BooleanProperty(default=False)
    seen_welcome = ndb.BooleanProperty(default=False)
    show_long_agenda = ndb.BooleanProperty(default=True)
    pending_change_email = ndb.TextProperty(default='', indexed=False)
    images = ndb.TextProperty(repeated=True)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
                The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)

    def set_email_to_pending(self):
        """ Changes the email address for the current user"""

        new_email = self.pending_change_email
        success = False
        if new_email != '':
            success, existing = \
                Unique.create_multi(['Member.auth_id:%s'%new_email,
                                     'Member.email_address:%s'%new_email])
            if not success:
                logging.error('Unable to create user for email %s because of \
                    duplicate keys' % new_email)
            else:
                # delete the old unique values
                Unique.delete_multi(['Member.auth_id:%s'%self.email_address,
                                     'Member.email_address:%s'%self.email_address])

                self.email_address=new_email
                self.auth_ids=[new_email]
            self.pending_change_email = ''
            self.put()

        if success:
            return new_email
        else:
            return None

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

    @classmethod
    def create_email_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'email')
        return entity.token

    @classmethod
    def delete_email_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'email', token).delete()

    @classmethod
    def create_invite_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'invite')
        return entity.token

    @classmethod
    def delete_invite_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'invite', token).delete()

    @classmethod
    def get_band_list(cls, req, the_member_key):
        """ check to see if this is in the session - if so, just use it """
        if 'member_bandlist' in req.session.keys():
            the_bands = req.session['member_bandlist']
        else:
            band_keys=assoc.get_band_keys_of_member_key(the_member_key, confirmed_only=True)
            the_bands = [bandkey.get() for bandkey in band_keys]

            req.session['member_bandlist'] = the_bands
        return the_bands

    @classmethod
    def get_add_gig_band_list(cls, req, the_member_key):
        """ check to see if this is in the session - if so, just use it """
        if 'member_addgigbandlist' in req.session.keys():
            the_manage_bands = req.session['member_addgigbandlist']
        else:
            band_keys=assoc.get_band_keys_of_member_key(the_member_key, confirmed_only=True)
            the_bands = ndb.get_multi(band_keys)
            the_manage_bands = []
            for b in the_bands:
                if b.anyone_can_manage_gigs or \
                    req.user.is_superuser or \
                    assoc.get_admin_status_for_member_for_band_key(req.user, b.key):
                    the_manage_bands.append(b)
            req.session['member_addgigbandlist'] = the_manage_bands
        return the_manage_bands

    @classmethod
    def invalidate_session_bandlists(cls, req):
        """ delete the bandlists from the session if they are changing """
        req.session.pop('member_bandlist',None)
        req.session.pop('member_addgigbandlist',None)
        
        
def create_new_member(email, name, password):
    if name=='':
        name=email
    unique_properties = ['email_address']
    user_data = Member.create_user(email,
        unique_properties,
        email_address=email, name=name, password_raw=password,
        verified=False, preferences=MemberPreferences())
    return user_data
        
        
def get_all_members(order=True, keys_only=False, verified_only=False):
    """ Return all member objects """

    args=[]
    if verified_only:
        args=[ndb.GenericProperty('verified')==True]

    if order:
        member_query = Member.query(*args).order(Member.lower_name)
    else:
        member_query = Member.query(*args)
    
    members = member_query.fetch(keys_only=keys_only)
    return members

def reset_motd():
    members=get_all_members()
    for m in members:
        m.seen_motd=False
    ndb.put_multi(members)

    
def forget_member_from_key(the_member_key):
    """ deletes a member, including all gig plans """

    # first find all of the assocs to bands
    the_assocs = assoc.get_assocs_of_member_key(the_member_key=the_member_key, confirmed_only=False)
    # delete all plans & abdicate as contact for gigs
    for an_assoc in the_assocs:
        plan.delete_plans_for_member_key_for_band_key(the_member_key, an_assoc.band)
        gig.reset_gigs_for_contact_key(the_member_key, an_assoc.band)

    # now quit the bands
    the_assoc_keys=[a.key for a in the_assocs]
    ndb.delete_multi(the_assoc_keys)

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

def get_member_from_email(the_email, keys_only=False):
    """ Return member object from email address """
    member = Member.get_by_auth_id(the_email)
    return member

def member_count_bands(the_member_key):
    return len(assoc.get_assocs_of_member_key(the_member_key, confirmed_only=True, keys_only=True))

def member_is_superuser(the_member):
    return the_member.is_superuser

def set_seen_motd_for_member_key(the_member_key):
    the_member = the_member_key.get()
    the_member.seen_motd = True
    the_member.put()

def set_seen_welcome_for_member_key(the_member_key):
    the_member = the_member_key.get()
    the_member.seen_welcome = True
    the_member.put()

def format_date_for_member(the_user, the_date, format="short"):
    the_locale='en'
    if the_user.preferences and the_user.preferences.locale:
        the_locale=the_user.preferences.locale
    the_str=''
    if format=='short':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="short"))
    elif format=='long':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="full"))
    elif format=='month':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="MMMM y"))
    elif format=='day':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="EEE"))
    elif format=='datepicker':
        # here we want the short format but replace the year with the complete year
        tmpstr=format_date(the_date,locale=the_locale,format="short")[:-2]
        the_str=tmpstr+str(the_date.year)
    return the_str
                            
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

        the_member_key=self.request.get("mk",'0')
        if the_member_key!='0':
            # if we've just edited this member, the database may not have
            # invalidated the cache. Therefore, use a method to get the 
            # member that uses an ancestor query.
            the_member=ndb.Key(urlsafe=the_member_key).get()
        else:
            return # todo what to do if it's not passed in?
            
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it

        ok_to_show = False
        same_band = False
        if the_member.key == the_user.key:
            is_me = True
            ok_to_show = True
        else:
            is_me = False
            
        # find the bands this member is associated with
        the_band_keys=assoc.get_band_keys_of_member_key(the_member_key=the_member.key, confirmed_only=True)
        
        if is_me == False:
            # are we at least in the same band, or superuser?
            if the_user.is_superuser:
                ok_to_show = True
            the_other_band_keys = assoc.get_band_keys_of_member_key(the_member_key=the_user.key, confirmed_only=True)
            for b in the_other_band_keys:
                if b in the_band_keys:
                    ok_to_show = True
                    same_band = True
                    break
            if ok_to_show == False:
                # check to see if we're sharing our profile - if not, bail!
                if (the_member.preferences and the_member.preferences.share_profile == False) and the_user.is_superuser == False:
                    return self.redirect('/')            

        email_change = self.request.get('e',False)
        if email_change:
            email_change_msg='You have selected a new email address - check your inbox to verify!'
        else:
            email_change_msg = None

        # if I'm not sharing my email, don't share my email
        show_email = False
        if the_member.key == the_user.key or the_user.is_superuser:
            show_email = True
        elif the_member.preferences and the_member.preferences.share_profile and the_member.preferences.share_email:
            show_email = True

        show_phone = False
        if the_member.key == the_user.key or the_user.is_superuser:
            show_phone = True
        else:
            # are we in the same band? If so, always show email and phone
            if same_band:
                show_phone = True
                show_email = True

        template_args = {
            'the_member' : the_member,
            'the_band_keys' : the_band_keys,
            'member_is_me' : the_user == the_member,
            'email_change_msg' : email_change_msg,
            'show_email' : show_email,
            'show_phone' : show_phone
        }
        self.render_template('member_info.html', template_args)


class EditPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)

    def _make_page(self, the_user):
        the_member_key=self.request.get("mk",'0')

        if the_member_key!='0':
            the_member = ndb.Key(urlsafe=the_member_key).get()
        else:
            the_member = None
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it

        if the_member==None:
            the_cancel_url=self.uri_for("agenda")
        else:
            the_cancel_url=self.uri_for("memberinfo",mk=the_member.key.urlsafe())
#            the_cancel_url="member_info.html?mk={0}".format(the_member.key.urlsafe())

        template_args = {
            'the_member' : the_member,
            'member_is_me' : the_user == the_member,
            'the_cancel_url' : the_cancel_url,
            'lang' : lang
        }
        self.render_template('member_edit.html', template_args)
                    

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""

        the_user = self.user            

        the_member_keyurl=self.request.get("mk",'0')
        
        if the_member_keyurl=='0':
            return # todo figure out what to do if we didn't find it
        else:
            the_member_key=ndb.Key(urlsafe=the_member_keyurl)
            
        if the_member_key is None:
            return # todo figure out what to do if we didn't find it

        the_member = the_member_key.get()

       # if we're changing email addresses, make sure we're changing to something unique
        member_email=self.request.get("member_email", None)
        if member_email is not None and member_email != '' and member_email != the_member.email_address:
            # store the pending address and invite the user to confirm it
            the_member.pending_change_email = member_email
            login.request_new_email(self, member_email)
        else:
            the_member.pending_change_email = ''
                   
        member_name=self.request.get("member_name", None)
        if member_name is not None and member_name != '':
            the_member.name=member_name
        else:
            member_name = None
                
        member_nickname=self.request.get("member_nickname", None)
        if member_nickname is not None:
            the_member.nickname=member_nickname
                
        member_phone=self.request.get("member_phone", None)
        if member_phone is not None:
            the_member.phone=member_phone

        member_statement=self.request.get("member_statement", None)
        if member_statement is not None:
            the_member.statement=member_statement

        image_blob = self.request.get("member_images",None)
        image_split = image_blob.split("\n")
        image_urls=[]
        for iu in image_split:
            the_iu=iu.strip()
            if the_iu:
                image_urls.append(the_iu)
        the_member.images=image_urls


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

        member_prefhidecanceledgigs=self.request.get("member_prefhidecanceledgigs", None)
        if (member_prefhidecanceledgigs):
            the_member.preferences.hide_canceled_gigs = True
        else:
            the_member.preferences.hide_canceled_gigs = False

        member_prefshareprofile=self.request.get("member_prefshareprofile", None)
        if (member_prefshareprofile):
            the_member.preferences.share_profile = True
        else:
            the_member.preferences.share_profile = False

        member_prefshareemail=self.request.get("member_prefshareemail", None)
        if (member_prefshareemail):
            the_member.preferences.share_email = True
        else:
            the_member.preferences.share_email = False

        member_preflocale=self.request.get("member_preflocale",None)
        if (member_preflocale):
            the_member.preferences.locale = member_preflocale
        else:
            the_member.preferences.locale = "en"
        

        the_member.put()                    

        if member_name:
            assoc.change_member_name(the_member_key, member_name)

        if (the_member.pending_change_email):
            return self.redirect(self.uri_for("memberinfo",mk=the_member.key.urlsafe(),e=1))
        else:
            return self.redirect(self.uri_for("memberinfo",mk=the_member.key.urlsafe()))


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
        
        the_assocs = assoc.get_assocs_of_member_key(the_member_key=the_member.key, confirmed_only=False)

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

class ManageBandsGetOtherBands(BaseHandler):
    """ return the popup of other bands """

    def post(self):    
        """ return the bands for a member """
        the_user = self.user

        the_member_key=self.request.get('mk','0')
        
        if the_member_key=='0':
            return # todo figure out what to do
            
        the_member_key=ndb.Key(urlsafe=the_member_key)
        the_band_keys=assoc.get_band_keys_of_member_key(the_member_key=the_member_key, confirmed_only=False)
                    
        every_band = band.get_all_bands()
        all_bands = [a_band for a_band in every_band if a_band.key not in the_band_keys]

        template_args = {
            'all_bands' : all_bands
        }
        self.render_template('member_band_popup.html', template_args)
    
            
class ManageBandsNewAssoc(BaseHandler):
    """ makes a new assoc for a member """                   

    def post(self):    
        """ makes a new assoc for a member """
        
        the_user = self.user
        
        the_member_key=self.request.get('mk','0')
        the_band_key=self.request.get('bk','0')
        
        if the_member_key=='0' or the_band_key=='0':
            return # todo figure out what to do
            
        the_member=ndb.Key(urlsafe=the_member_key).get()
        the_band=ndb.Key(urlsafe=the_band_key).get()
        
        if assoc.get_assoc_for_band_key_and_member_key(the_band_key = the_band.key, the_member_key = the_member.key) is None:
            assoc.new_association(the_member, the_band)        
            goemail.send_new_member_email(the_band,the_member)
        
        # since our bands are changing, invalidate the band list in our session
        self.user.invalidate_session_bandlists(self)
 

class ManageBandsDeleteAssoc(BaseHandler):
    """ deletes an assoc for a member """                   

    def get(self):    
        """ deletes an assoc for a member """
        
        the_user = self.user
        
        the_assoc_keyurl=self.request.get('ak','0')

        if the_assoc_keyurl=='0':
            return # todo figure out what to do
        
        the_assoc=ndb.Key(urlsafe=the_assoc_keyurl).get()
        
        the_member_key=the_assoc.member
        the_band_key=the_assoc.band

        assoc.delete_association_from_key(the_assoc.key)
        plan.delete_plans_for_member_key_for_band_key(the_member_key, the_band_key)
        gig.reset_gigs_for_contact_key(the_member_key, the_band_key)

        # since our bands are changing, invalidate the band list in our session
        self.user.invalidate_session_bandlists(self)
        
        return self.redirect('/member_info.html?mk={0}'.format(the_member_key.urlsafe()))
        
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
        
        assoc.set_default_section(the_member_key, the_band_key, the_section_key)

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
        
        assoc.set_multi(the_member_key, the_band_key, (the_do=='true'))


class AdminPage(BaseHandler):
    """ Page for member administration """

    @user_required
    def get(self):
        if member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/agenda.html')            
            
    def _make_page(self,the_user):
    
        # get all the admin members
        all_band_keys = band.get_all_bands(keys_only=True)
        all_admin_keys = []
        for bk in all_band_keys:
            admin_member_keys = assoc.get_admin_members_from_band_key(bk, keys_only=True)
            for amk in admin_member_keys:
                if not amk in all_admin_keys:
                    all_admin_keys.append(amk)
                    
        all_admin_members = ndb.get_multi(all_admin_keys)
        all_admin_emails = [a.email_address for a in all_admin_members]
        
        template_args = {
            'all_admin_emails' : all_admin_emails
        }
        self.render_template('member_admin.html', template_args)

class AdminPageAllMembers(BaseHandler):
    """ Page for member administration """

    @user_required
    def post(self):
        if member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return;
            
    def _make_page(self,the_user):
    
        the_members = get_all_members(verified_only=True)

        member_band_info={}
        for a_member in the_members:
            assocs=assoc.get_assocs_of_member_key(a_member.key, confirmed_only=False)
            member_band_info[a_member.key] = assocs
        
        template_args = {
            'the_members' : the_members,
            'the_band_info' : member_band_info
        }
        self.render_template('member_admin_memberlist.html', template_args)


class AdminPageInviteMembers(BaseHandler):
    """ Page for member administration """
    
    @user_required
    def post(self):
        if member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return;

    def _make_page(self,the_user):
    
        the_invite_assocs = assoc.get_all_invites()
        
        template_args = {
            'the_assocs' : the_invite_assocs
        }
        self.render_template('member_admin_invitelist.html', template_args)


class AdminPageSignupMembers(BaseHandler):
    """ Page for member administration """

    @user_required
    def post(self):
        if member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return;
            
    def _make_page(self,the_user):
    
        # todo make sure the user is a superuser
        
        the_tokens = login.get_all_signup_tokens()
        
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=2)
        limit = now - delta
        for a_token in the_tokens:
            the_member = Member.get_by_id(int(a_token.user))
            if the_member:
                a_token.email = the_member.email_address
            else:
                a_token.email = None

            if a_token.created < limit:
                a_token.is_old=True
        
        template_args = {
            'the_tokens' : the_tokens
        }
        self.render_template('member_admin_signuplist.html', template_args)

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
        
class GetBandList(BaseHandler):
    """ return a list of bands """
    
    @user_required
    def post(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        if the_member_keyurl=='0':
            return # todo figure out what to do
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_bands = self.user.get_band_list(self, the_member_key)

        template_args = {
            'the_bands' : the_bands
        }
        self.render_template('navbar_bandlist.html', template_args)            

class GetAddGigBandList(BaseHandler):
    """ return a list of bands """
    
    @user_required
    def post(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        if the_member_keyurl=='0':
            return # todo figure out what to do
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_manage_bands = self.user.get_add_gig_band_list(self, the_member_key)
            
        template_args = {
            'the_bands' : the_manage_bands
        }
        self.render_template('navbar_addgigbandlist.html', template_args)
        
class RewriteAll(BaseHandler):
    """ get all member objects from the database, and write them back. this will force """
    """ an update to the structure, useful when adding properties. But ugly. """
    
    @user_required
    def get(self):
        the_members = get_all_members(order=False)
        ndb.put_multi(the_members)

        the_assocs = assoc.get_all_assocs()
        ndb.put_multi(the_assocs)

        self.redirect(self.uri_for('memberadmin'))
        
        
class DeleteInvite(BaseHandler):
    """ remove association with band """
    
    @user_required
    def get(self):
        """ post handler - wants an ak """

        the_assoc_keyurl=self.request.get('ak','0')

        if the_assoc_keyurl=='0':
            return # todo figure out what to do

        the_assoc_key = ndb.Key(urlsafe=the_assoc_keyurl)
        the_assoc = the_assoc_key.get()
        
        # make sure we're a band admin or a superuser
        if not (self.user.is_superuser or assoc.get_admin_status_for_member_for_band_key(self.user, the_assoc.band)):
            return self.redirect('/agenda.html')

        the_band_key = the_assoc.band

        the_member_key = the_assoc.member
        assoc.delete_association_from_key(the_assoc_key) 

        invites = assoc.get_inviting_assoc_keys_from_member_key(the_member_key)
        if invites is None or (len(invites)==1 and invites[0]==the_assoc_key):
            logging.error('removed last invite from member; deleteing')
            forget_member_from_key(the_member_key)            
                    
        return self.redirect('/band_info.html?bk={0}'.format(the_band_key.urlsafe()))
