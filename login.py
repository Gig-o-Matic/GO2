"""
Handlers for user-related pages: login, logout, signup, verify
"""

from google.appengine.api import users
from webapp2_extras.auth import *
from requestmodel import *

import logging
import member
import goemail

ENABLE_EMAIL = False

class LoginPage(BaseHandler):
    def get(self):
        self._serve_page()

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        try:
            u = self.auth.get_user_by_password(email, password, remember=True,
                save_session=True)
            self.redirect(self.uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', email, type(e))
            self._serve_page(True)

    def _serve_page(self, failed=False):
        username = self.request.get('username')
        params = {
            'username': username,
            'failed': failed
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
        self.render_template('signup.html')

    def post(self):
        email = self.request.get('email')
        name = self.request.get('name')
        password = self.request.get('password')
        last_name = self.request.get('lastname')

        unique_properties = ['email_address']
        user_data = self.user_model.create_user(email,
            unique_properties,
            email_address=email, name=name, password_raw=password,
            verified=False)
        if not user_data[0]: #user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
                duplicate keys %s' % (name, user_data[1]))
            return
        
        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='v', user_id=user_id,
            signup_token=token, _full=True)

        if ENABLE_EMAIL:
            if goemail.send_registration_email(email, verification_url):
                msg = "An email has been sent - check your inbox! {0}".format(verification_url)
            else:
                msg = "Email failed!"
        else:
            msg = 'Verification link is <a href="{0}">{0}</a>'.format(verification_url)
            
        self.display_message(msg)

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
            logging.info( \
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

            self.display_message('User email address has been verified. Proceed <a href="/login">here</a>')
            return
        elif verification_type == 'p':
            # supply user to the page
            params = {
                'user': user,
                'token': signup_token
            }
            self.render_template('resetpassword.html', params)
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
    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='p', user_id=user_id,
      signup_token=token, _full=True)

    if ENABLE_EMAIL:
        if goemail.send_forgot_email(user_id, verification_url):
            msg = "An email has been sent - check your inbox! {0}".format(url)
        else:
            msg = "Email failed!"
    else:
        msg = 'Send an email to user in order to reset their password. \
              They will be able to do so by visiting <a href="{url}">{url}</a>'

    self.display_message(msg.format(url=verification_url))
  
  def _serve_page(self, not_found=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'not_found': not_found
    }
    self.render_template('forgot.html', params)

config = {
    'webapp2_extras.auth': {
        'user_model': 'models.User',
        'user_attributes': ['name']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

# app = webapp2.WSGIApplication([
#           webapp2.Route('/', MainHandler, name='home'),
#           webapp2.Route('/signup', SignupHandler),
#           webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
#               handler=VerificationHandler, name='verification'),
#           webapp2.Route('/password', SetPasswordHandler),
#           webapp2.Route('/login', LoginHandler, name='login'),
#           webapp2.Route('/logout', LogoutHandler, name='logout'),
#           webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
#           webapp2.Route('/authenticated', AuthenticatedHandler, name='authenticated')
# ], debug=True, config=config)
# 
# logging.getLogger().setLevel(logging.DEBUG)
