import webapp2
from google.appengine.api import mail
from google.appengine.api import users

SENDER_EMAIL = 'aoppenheimer@gmail.com'

def send_registration_email(the_email, the_url):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    
    message.body = """
Hello! You have registered to join Gig-O-Matic - click the link below to continue the process.

{0}

Thanks,
The Gig-O-Matic Team

    """.format(the_url)

    message.send()
    return True
    
    
def send_forgot_email(the_email, the_url):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    
    message.body = """
Hello! To reset your Graph-O-Matic password, click the link below.

{0}

Thanks,
The Gig-O-Matic Team

    """.format(the_url)

    message.send()
    return True
