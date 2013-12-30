"""
Handlers for user-related pages: login, logout, signup, verify
"""

from google.appengine.api import users
from webapp2_extras.auth import *
from requestmodel import *
from webapp2_extras.appengine.auth.models import UserToken
from google.appengine.ext import ndb

import logging
import member
import goemail
import datetime

ENABLE_EMAIL = True

class LoginPage(BaseHandler):
    def get(self):
        the_url = self.request.get('originalurl',None)
        self._serve_page(the_url=the_url)

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        remember = self.request.get('remember',False)
        if remember:
            remember = True
        
        try:
            u = self.auth.get_user_by_password(email, password, remember=remember,
                save_session=True)

            the_url = self.request.get('originalurl',None)
            if the_url:
                self.redirect(str(the_url))
            else:
                self.redirect(self.uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self._serve_page(failed=True)

    def _serve_page(self, the_url=None, failed=False):
        username = self.request.get('username')
        params = {
            'title' : 'Login',        
            'username': username,
            'failed': failed,
            'originalurl': the_url
        }
        self.render_template('login.html', params)

class LogoutHandler(BaseHandler):
    def get(self):
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
        email = self.request.get('email')
        name = self.request.get('name')
        password = self.request.get('password')

        if name=='':
            name=email

        unique_properties = ['email_address']
        user_data = self.user_model.create_user(email,
            unique_properties,
            email_address=email, name=name, password_raw=password,
            verified=False, preferences=member.MemberPreferences())
        if not user_data[0]: #user_data is a tuple
            self._serve_page(self,failed=True)
            return
        
        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='v', user_id=user_id,
            signup_token=token, _full=True)

        if not ENABLE_EMAIL:
            msg=verification_url
        else:
            goemail.send_registration_email(email, verification_url)
            msg=''

        params = {
            'title' : 'Signed Up',        
            'msg':msg
        }
        self.render_template('confirm_signup.html', params)
            
    def _serve_page(self, the_url=None, failed=False):
    
        params = {
            'title' : 'Sign Up',        
            'failed': failed,
        }
        self.render_template('signup.html', params)


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
            self.abort(404)
        
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
                'title' : 'Reset Password',            
                'user': user,
                'token': signup_token
            }
            self.render_template('resetpassword.html', params)
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
            self.render_template('confirm_email_change.html', template_args)            
        else:
            logging.info('verification type not supported')
            self.abort(404)

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
        self.render_template('authenticated.html')

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
        goemail.send_forgot_email(user.email_address, verification_url)
        msg=""
    else:
        msg = verification_url

    params = {
        'title' : 'Signed Up',
        'msg' : msg
    }
    self.render_template('confirm_forgot.html', params)
  
  def _serve_page(self, not_found=False):
    username = self.request.get('username')
    params = {
        'title' : 'Reset Password',    
        'username': username,
        'not_found': not_found
    }
    self.render_template('forgot.html', params)

##########
#
# CheckEmail - verifies an email address is available
#
##########
class CheckEmail(BaseHandler):

    def post(self):
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

    goemail.send_the_pending_email(the_new_address, verification_url)
    

def get_all_signup_tokens():
    """ Return UserToken objects with subject 'signup' """
    token_query = UserToken.query(UserToken.subject=='signup').order(UserToken.created)
    tokens = token_query.fetch()
    return tokens
    
##########
#
# auto delete old signup tokens - we don't want them hanging around forever
#
##########
class AutoDeleteSignupTokenHandler(BaseHandler):
    """ automatically delete old tokens """
    def get(self):
        the_tokens = get_all_signup_tokens()
        
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=2)
        limit = now - delta
        the_old_tokens=[a_token for a_token in the_tokens if a_token.created < limit]
        
#         goemail.notify_superuser_of_old_tokens(len(the_old_tokens))
#         if len(the_old_tokens) > 0:
        logging.info("deleted {0} unused signup tokens".format(len(the_old_tokens)))

        for a_token in the_old_tokens:
            a_token.key.delete()
