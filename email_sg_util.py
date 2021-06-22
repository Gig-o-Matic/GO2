"""

 sendgrid api utils for Gig-o-Matic 2 

 Aaron Oppenheimer
 21 June 2021

"""

from requestmodel import *

import email_sg_db
import member


# handler function for email sg admin key admin

class AdminPage(BaseHandler):
    """ Page for sendgrid_api administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):
    
        template_args = {
            'current' : email_sg_db.get_sendgrid_api()
        }

        print(template_args)

        self.render_template('email_sg_admin.html', template_args)


    @user_required
    def post(self):
        the_sendgrid_api=self.request.get('sendgrid_api_content','')

        email_sg_db.set_sendgrid_api(the_sendgrid_api)
                
        self.redirect(self.uri_for('email_sg_admin'))

