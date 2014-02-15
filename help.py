from google.appengine.api import users

from requestmodel import *

import webapp2
import logging
import goemail

class HelpHandler(BaseHandler):

    @user_required
    def get(self):    
        """ get handler for help page """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for help """

        template_args = {
            'help_is_active' : True
        }
        self.render_template('help.html', template_args)


class SignUpBandHandler(BaseHandler):

    def get(self):    
        """ get handler for help page """
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        """ construct page for help """

        template_args = {
            'help_is_active' : True
        }
        self.render_template('help_band_request.html', template_args)

    def post(self):
        """ handles requests for new bands """
        
        the_email = self.request.get('email',None)
        the_name = self.request.get('name',None)
        the_info = self.request.get('info',None)

        goemail.send_band_request_email(the_email, the_name, the_info)

        params = {
            'msg': ''
        }
        self.render_template('confirm_band_request.html', params)
