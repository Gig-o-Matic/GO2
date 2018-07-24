"""
Base class for webapp2 request handlers
"""

# from jinja2env import jinja_environment as je

from google.appengine.ext import ndb

import os.path
import webapp2

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras import i18n
from webapp2_extras import jinja2

import logging
import motd_db
import sys

import gigoexceptions

def user_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            if self.request.path=='/':
                locale=self.request.get('locale',None)
                if locale:
                    self.redirect(self.uri_for('login',locale=locale),abort=True)
                else:
                    self.redirect(self.uri_for('login'),abort=True)
            else:
                self.redirect(self.uri_for('login',originalurl=self.request.url),abort=True)            
        else:
            u = self.user_info
            user = self.user_model.get_by_id(u['user_id'])
            user.put()
            return handler(self, *args, **kwargs)

    return check_login


def superuser_required(handler):
    """
        Decorator that makes sure there's a user logged in, then makes sure it's a
        superuser.
    """
    
    def check_superuser(self, *args, **kwargs):
        user=self.user
        if not user or not user.is_superuser:
            self.redirect(self.uri_for('login',originalurl=self.request.url),abort=True)            
        else:
            return handler(self, *args, **kwargs)

    return check_superuser
    

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

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, filename, args):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(filename, **args)
        self.response.write(rv)

    def render_template(self, filename, params=None):
        if not params:
            params = {}

        # override locale if set in params
        if params and 'locale' in params.keys():
            i18n.get_i18n().set_locale(params['locale'])

        is_superuser = False
        if self.user:
            is_superuser = self.user.is_superuser

        is_betatester = False
        if self.user:
            is_betatester = self.user.is_betatester

        params['the_user'] = self.user
        params['the_user_is_superuser'] = is_superuser
        params['the_user_is_betatester'] = is_betatester
        if self.user:
            params['the_user_addgigbandlist'] = self.user.get_add_gig_band_list(self, self.user.key)
        params['logout_link'] = self.uri_for('logout')
        if self.user is not None and not self.user.seen_welcome:
            params['welcome'] = True
        if self.user is not None and not self.user.seen_motd:
            params['motd'] = motd_db.get_motd()
        self.render_response(filename, params)

    def render_nouser_template(self, filename, params=None):
        if not params:
            params = {}

        params['the_user'] = None
        params['the_user_is_superuser'] = False
        params['the_user_is_betatester'] = False
        self.render_response(filename, params)

    def display_message(self, message):
        """Utility function to display a template with a simple message."""
        params = {
            'message': message
        }
        self.render_template('message.html', params)

    # this is needed for webapp2 sessions to work
    def dispatch(self):

        # for requests still going to appspot, redirect
        request = self.request
        if request.host.startswith("gig-o-matic.appspot.com") or request.host.startswith("gig-o-matic.com"):
            import urlparse
            scheme, netloc, path, query, fragment = urlparse.urlsplit(request.url)

            # the cron stuff should not redirect
            if not path.startswith("/admin_"):
                url = urlparse.urlunsplit([scheme, "www.gig-o-matic.com", path, query, fragment])
                # Send redirect
                self.redirect(url, permanent=True, abort=True)

        if request.host.startswith("127.0.0.1"):
            import urlparse
            scheme, netloc, path, query, fragment = urlparse.urlsplit(request.url)

            # the cron stuff should not redirect
            if not path.startswith("/admin_"):
                url = urlparse.urlunsplit([scheme, "localhost:8080", path, query, fragment])
                # Send redirect
                self.redirect(url, permanent=True, abort=True)



        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        # Set locale on each request right away, to make it available to both
        # templates and backend Python code
        if self.request.get("locale"):
            locale = self.request.get("locale")
        elif self.user and self.user.preferences.locale:
            locale = self.user.preferences.locale
        else:
            locale = None
        i18n.get_i18n().set_locale(locale)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        except gigoexceptions.GigoException as error:
            logging.error( "Exception: %s" % error )
            self.render_template('error.html', [])
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    # create a way for one member to invalidate another's bandlist cache
    def set_member_cache_dirty(self,member_key):
        app = webapp2.get_app()
        dirty_list = app.registry.get('member_dirty_cache_list')
        if not dirty_list:
            dirty_list = []
        if not member_key in dirty_list:
            dirty_list.append(member_key)
        app.registry['member_dirty_cache_list'] = dirty_list
        
    # see if a member key is dirty
    def member_cache_is_dirty(self, member_key):
        app = webapp2.get_app()
        dirty_list = app.registry.get('member_dirty_cache_list')
        if not dirty_list or member_key not in dirty_list:
            return False
        else:
            return True
            
    # remove member from dirty_list
    def member_cache_set_clean(self, member_key):   
        app = webapp2.get_app()
        dirty_list = app.registry.get('member_dirty_cache_list')
        if not dirty_list or member_key not in dirty_list:
            return
        else:
            dirty_list.remove(member_key)
            app.registry['member_dirty_cache_list'] = dirty_list
