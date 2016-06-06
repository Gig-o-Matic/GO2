"""
Handlers for user-related pages: login, logout, signup, verify
"""

from google.appengine.api import users
from webapp2_extras.auth import *
from requestmodel import *
from webapp2_extras.appengine.auth.models import UserToken
from webapp2_extras.appengine.auth.models import User
from google.appengine.ext import ndb

import logging
import member
import goemail
import datetime
import lang
import assoc

ENABLE_EMAIL = True

class LoginPage(BaseHandler):
    def get(self):
        the_url = self.request.get('originalurl',None)
        self._serve_page(the_url=the_url)

    def post(self):
        email = self.request.get('email').lower()
        password = self.request.get('password')
        remember = self.request.get('remember',False)
        if remember:
            remember = True
        
        try:
            u = self.auth.get_user_by_password(email, password, remember=remember,
                save_session=True)

            
            the_user = self.user_model.get_by_id(u['user_id'])

            if the_user.verified is False:
                self.session.clear()
                self.auth.unset_session()            
                self._serve_page(unverified=True)
            else:
                the_url = self.request.get('originalurl',None)
                if the_url:
                    self.redirect(str(the_url))
                else:
                    self.redirect(self.uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self._serve_page(failed=True)

    def _serve_page(self, the_url=None, failed=False, unverified=False):
        username = self.request.get('username')

        locale=self.request.get('locale','en')

        params = {
            'username': username,
            'failed': failed,
            'unverified': unverified,
            'originalurl': the_url,
            'locale': locale,
            'languages': lang.LOCALES
        }
        self.render_template('login.html', params=params)

class LogoutHandler(BaseHandler):
    def get(self):
        # if you actually log out, we'll clear the session to reset band lists and stuff
        self.session.clear()
        self.auth.unset_session()
        self.redirect(self.uri_for('home'))


##########
#
# SignupHandler
#
##########
class SignupPage(BaseHandler):
    """ class for handling signup requests """
    def get(self):
        self._serve_page(self, failed=False)

    def post(self):
        email = self.request.get('email').lower()
        name = self.request.get('name')
        password = self.request.get('password')

        user_data = member.create_new_member(email=email, name=name, password=password)
        if not user_data[0]: #user_data is a tuple
            self._serve_page(self,failed=True)
            return
        
        user = user_data[1]
        user_id = user.get_id()

        locale = self.request.get('locale','en')
        user.preferences.locale=locale
        user.put()

        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='v', user_id=user_id,
            signup_token=token, _full=True)

        if not ENABLE_EMAIL:
            msg=verification_url
        else:
            goemail.send_registration_email(the_req=self, the_email=email, the_url=verification_url)
            msg=''

        params = {
            'msg': msg,
            'locale': locale
        }
        self.render_template('confirm_signup.html', params=params)
            
    def _serve_page(self, the_url=None, failed=False):
    
        locale=self.request.get('locale',None)

        params = {
            'failed': failed,
            'locale' : locale
        }
        self.render_template('signup.html', params=params)


##########
#
# VerificationHandler
#
##########
class VerificationHandler(BaseHandler):
    """ handles user verification """
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id),
                                                     signup_token,
                                                    'signup')

        if not user:
            logging.error( \
                'Could not find any user with id "%s" signup token "%s"',
                user_id, signup_token)
            locale=self.request.get('locale',None)
            if locale:
                self.redirect('{0}?locale={1}'.format(self.uri_for('linkerror'),locale))
            else:
                self.redirect(self.uri_for('linkerror'))
            return
        
        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_signup_token(user.get_id(), signup_token)

            if not user.verified:
                user.verified = True
                user.put()
            self.auth.unset_session()

#             self.display_message('User email address has been verified. Proceed <a href="/login">here</a>')
            self.redirect(self.uri_for('login'))

        elif verification_type == 'p':
            # supply user to the page
            params = {
                'user': user,
                'token': signup_token
            }
            self.render_template('resetpassword.html', params=params)
        else:
            logging.info('verification type not supported')
            self.abort(404)

##########
#
# EmailVerificationHandler
#
##########
class EmailVerificationHandler(BaseHandler):
    """ handles user verification """
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id),
                                                     signup_token,
                                                    'email')

        if not user:
            logging.error( \
                'Could not find any user with id "%s" signup token "%s"',
                user_id, signup_token)
            self.abort(404)
        
        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'e':
            new_email = user.set_email_to_pending()
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_email_token(user.get_id(), signup_token)
            template_args = {
                'success' : new_email != None,
                'the_email' : new_email
            }
            self.render_template('confirm_email_change.html', params=template_args)            
        else:
            logging.info('verification type not supported')
            self.abort(404)

##########
#
# InviteVerificationHandler
#
##########
class InviteVerificationHandler(BaseHandler):
    """ handles user invite verification """
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id),
                                                     signup_token,
                                                    'invite')
                                                    
        if not user:
            logging.error( \
                'Could not find any user with id "%s" invite token "%s"',
                user_id, signup_token)
            locale=self.request.get('locale',None)
            if locale:
                self.redirect('{0}?locale={1}'.format(self.uri_for('linkerror'),locale))
            else:
                self.redirect(self.uri_for('linkerror'))
            return
        
        if verification_type == 'i':
            # ok, this is a user who has one or more invites pending. They have a user but
            # not a password. We need to do this:
            #   - direct them to a welcome page where they can enter a password
            template_args = {
                'mk': user.key.urlsafe(),
                'st': signup_token,
                'locale': user.preferences.locale
            }
            self.render_template('invite_welcome.html', params=template_args)            
        else:
            logging.info('verification type not supported')
            self.abort(404)
            
    def post(self):
        mk = self.request.get('mk', None)
        st = self.request.get('st', None)
        password = self.request.get('password')
        
        if mk is None or st is None:
            self.abort(404)
            
        the_member = ndb.Key(urlsafe = mk).get()

        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(the_member), remember=True)

        #   - invalidate the invite link so they can't use it again
        self.user_model.delete_invite_token(the_member.get_id(), st)

        #   - turn their 'invite' assocs into real assocs
        assoc.confirm_invites_for_member_key(the_member.key)

        the_member.set_password(password)
        the_member.verified = True

        name = self.request.get('member_name', '')
        nickname = self.request.get('member_nickname', '')

        if name != '':
            the_member.name=name
        if nickname  != '':
            the_member.nickname=nickname
        
        the_member.put()

        self.redirect(self.uri_for('home'))


        
##########
#
# SetPasswordHandler
#
##########
class SetPasswordHandler(BaseHandler):

  @user_required
  def post(self):
    password = self.request.get('password')
    old_token = self.request.get('t')

    if not password or password != self.request.get('confirm_password'):
      self.display_message('passwords do not match')
      return

    user = self.user
    user.set_password(password)
    user.put()

    # remove signup token, we don't want users to come back with an old link
    self.user_model.delete_signup_token(user.get_id(), old_token)
    
#    self.display_message('Password updated')
    self.auth.unset_session()
    self.redirect(self.uri_for('home'))

##########
#
# AuthenticatedHandler
#
##########
class AuthenticatedHandler(BaseHandler):
    @user_required
    def get(self):
        self.render_template('authenticated.html', params=None)

##########
#
# LinkErrorHandler
#
##########
class LinkErrorHandler(BaseHandler):
    def get(self):
        locale=self.request.get('locale',None)
        if locale:
            args={
                'locale': locale
            }
        else:
            args = None
        self.render_template('link_error.html', params=args)

##########
#
# ForgotPasswordHandler
#
##########
class ForgotPasswordHandler(BaseHandler):
  def get(self):
    self._serve_page()

  def post(self):
    username = self.request.get('username')

    user = self.user_model.get_by_auth_id(username)
    if not user:
      logging.info('Could not find any user entry for username %s', username)
      self._serve_page(not_found=True)
      return

    user_id = user.get_id()
    token = member.Member.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='p', user_id=user_id,
      signup_token=token, _full=True)

    if ENABLE_EMAIL:
        goemail.send_forgot_email(the_req=self, the_email=user.email_address, the_url=verification_url)
        msg=""
    else:
        msg = verification_url

    locale=self.request.get('locale',None)

    params = {
        'msg' : msg,
        'locale' : locale
    }
    self.render_template('confirm_forgot.html', params=params)
  
  def _serve_page(self, not_found=False):
  
    locale=self.request.get('locale',None)

    username = self.request.get('username')
    params = {
        'username': username,
        'not_found': not_found,
        'locale' : locale
    }
    self.render_template('forgot.html', params=params)

##########
#
# CheckEmail - verifies an email address is available
#
##########
class CheckEmail(BaseHandler):

    def post(self):
        if self.user.is_superuser:
            logging.info("superuser overriding email check")        
            self.response.write('true')
        else:
            test_email = self.request.get('member_email')
            email_ok = 'true'
            if test_email != self.user.email_address:
                if self.user_model.get_by_auth_id(test_email):
                    email_ok = 'false'
            self.response.write(email_ok)
        


##########
#
# request_new_email
#
##########
def request_new_email(the_request, the_new_address):
    """"    if a member has asked for a new email address, send a confirmation email, and
            if it comes back, make the change. """
            
    # in theory, we've already verified that the email is unique - we'll trust that
    
    # set up a token
    user_id = the_request.user.get_id()
    token = the_request.user_model.create_email_token(user_id)

    verification_url = the_request.uri_for('emailverification', type='e', user_id=user_id,
            signup_token=token, _full=True)

    goemail.send_the_pending_email(the_req=the_request, the_email_address=the_new_address, the_confirm_link=verification_url)
    

def get_all_signup_tokens():
    """ Return query with subject 'signup' """

    signupTokensQuery = UserToken.query(UserToken.subject=='signup')
    signupTokens = signupTokensQuery.fetch()
    return signupTokens

def get_old_signup_tokens():
    """ Return query with subject 'signup' """

    expiredTokensQuery = UserToken.query(UserToken.subject=='signup', UserToken.created <= (datetime.datetime.utcnow() - datetime.timedelta(days=2)))
    expiredTokens = expiredTokensQuery.fetch(keys_only=True)
    return expiredTokens
    
def get_old_auth_tokens():
    """ Return query with subject 'auth' """

    expiredTokensQuery = UserToken.query(UserToken.subject=='auth', UserToken.created <= (datetime.datetime.utcnow() - datetime.timedelta(weeks=3)))
    expiredTokens = expiredTokensQuery.fetch(keys_only=True)
    return expiredTokens


##########
#
# auto delete old signup tokens - we don't want them hanging around forever
#
##########
class AutoDeleteSignupTokenHandler(BaseHandler):
    """ automatically delete old tokens """
    def get(self):
        the_token_keys = get_old_signup_tokens()
        logging.info("deleting {0} unused signup tokens".format(len(the_token_keys)))
        if len(the_token_keys):
            ndb.delete_multi(the_token_keys)

        the_token_keys = get_old_auth_tokens()
        logging.info("deleting {0} old auth tokens".format(len(the_token_keys)))
        if len(the_token_keys):
            ndb.delete_multi(the_token_keys)
            
#        member.update_all_uniques()
#        member.clean_up_verified()
#        assoc.update_all_assocs()

class WhatisPageHandler(BaseHandler):
    """ handle the whatis page """
    
    def get(self):
        params = {}
        self.render_template('whatis.html', params=params)
    