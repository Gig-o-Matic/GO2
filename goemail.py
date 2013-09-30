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
    message.subject = 'Welcome to Gig-O-Matic'
    message.body = """
Hello! You have registered to join Gig-O-Matic - click the link below to continue the process.

{0}

Thanks,
The Gig-O-Matic Team

    """.format(the_url)

    message.send()
    return True

def send_band_accepted_email(the_email, the_band_name):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = 'Gig-O-Matic: Confirmed!'
    message.body = """
Hello! You have been confirmed as a member of {0} and can now start using Gig-O-Matic to manage stuff.

Thanks,
The Gig-O-Matic Team

    """.format(the_band_name)

    message.send()
    return True
    
    
def send_forgot_email(the_email, the_url):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = 'Gig-O-Matic Password Reset'
    message.body = """
Hello! To reset your Gig-O-Matic password, click the link below.

{0}

Thanks,
The Gig-O-Matic Team

    """.format(the_url)

    message.send()
    return True
