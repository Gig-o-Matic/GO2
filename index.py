from google.appengine.api import users

import webapp2
from jinja2env import jinja_environment as je
import make_test

    
class MainPage(webapp2.RequestHandler):

    def get(self):
    
        user = users.get_current_user()

        if user:
            make_test.test_band()       
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
            
class TestMail(webapp2.RequestHandler):

    def get(self):
        from google.appengine.api import mail

        mail.send_mail(sender="Example.com Support <support@example.com>",
                      to="Aaron Oppenheimer <aoppenheimer@gmail.com>",
                      subject="Your account has been approved",
                      body="""
        Dear Albert:

        Your example.com account has been approved.  You can now visit
        http://www.example.com/ and sign in using your Google Account to
        access new features.

        Please let us know if you have any questions.

        The example.com Team
        """)
