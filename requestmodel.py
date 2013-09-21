"""
Base class for webapp2 request handlers
"""

from jinja2env import jinja_environment as je
from google.appengine.ext import ndb

#import logging
import os.path
import webapp2

from webapp2_extras import auth
from webapp2_extras import sessions

def user_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            self.redirect(self.uri_for('login'), abort=True)
        else:
            return handler(self, *args, **kwargs)

    return check_login

class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth()

    @webapp2.cached_property
    def user_info(self):
        """Shortcut to access a subset of the user attributes that are stored
        in the session.

        The list of attributes to store in the session is specified in
            config['webapp2_extras.auth']['user_attributes'].
        :returns
            A dictionary with most user information
        """
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        """Shortcut to access the current logged in user.

        Unlike user_info, it fetches information from the persistence layer and
        returns an instance of the underlying model.

        :returns
            The instance of the user model associated to the logged in user.
        """
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.

        It is consistent with config['webapp2_extras.auth']['user_model'], if set.
        """      
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
            """Shortcut to access the current session."""
            return self.session_store.get_session(backend="datastore")

    def render_template(self, filename, params=None):
        if not params:
            params = {}

        params['the_user'] = self.user
        params['logout_link'] = self.uri_for('logout')
        print 'user is {0}'.format(self.user)
        template = je.get_template(filename)
        self.response.write(template.render(params))

    def display_message(self, message):
        """Utility function to display a template with a simple message."""
        params = {
            'message': message
        }
        self.render_template('message.html', params)

    # this is needed for webapp2 sessions to work
    def dispatch(self):
            # Get a session store for this request.
            self.session_store = sessions.get_store(request=self.request)

            try:
                    # Dispatch the request.
                    webapp2.RequestHandler.dispatch(self)
            finally:
                    # Save all sessions.
                    self.session_store.save_sessions(self.response)
