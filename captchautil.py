"""

 captcha utils for Gig-o-Matic 2 

 Aaron Oppenheimer
 6 June 2020

"""

from requestmodel import *

import captcha_db
import member

# handler function for captcha key admin

class AdminPage(BaseHandler):
    """ Page for captcha key administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):
    
        current = captcha_db.get_captchakeys()
        if current:
            site= current.site_key
            secret = current.secret_key
        else:
            site = None
            secret = None

        template_args = {
            'current_site' : site,
            'current_secret' : secret
        }
        self.render_template('captcha_admin.html', template_args)


    @user_required
    def post(self):
        the_site = self.request.get('sitekey_content','')
        the_secret = self.request.get('secretkey_content','')

        captcha_db.set_captchakeys(site_key=the_site, secret_key=the_secret)
        
        self.redirect(self.uri_for('captcha_admin'))

