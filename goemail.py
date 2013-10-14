import webapp2
from google.appengine.api import mail
from google.appengine.api import users
import band
import gig
import member

SENDER_EMAIL = 'gigomatic.superuser@gmail.com'

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
    
##########
#
# send an email announcing a new gig
#
##########    
def send_newgig_email(the_email_address, the_gig, the_band, the_gig_url):
    if not mail.is_email_valid(the_email_address):
        return False
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = 'Gig-O-Matic New Gig'
    message.body = """
Hello! A new gig has been added to the Gig-O-Matic for your band {0}:

{1}
Date: {2}

{3}

Can you make it? You can (and should!) weigh in here: {4}

Thanks,
The Gig-O-Matic Team

    """.format(the_band.name, the_gig.title, the_gig.date, the_gig.details, the_gig_url)
    message.send()
    return True


def announce_new_gig(the_gig, the_gig_url):
    the_band_key = the_gig.key.parent()
    the_band=the_band_key.get()
    the_members = member.get_member_keys_of_band_key(the_band_key)
    for the_member_key in the_members:
        the_member = the_member_key.get()
        if the_member.preferences:
            if the_member.preferences.email_new_gig:
                send_newgig_email(the_member.email_address, the_gig, the_band, the_gig_url)
        

def send_new_member_email(band,new_member):
    members=member.get_admin_members_from_band_key(band.key)
    for the_member in members:
        send_the_new_member_email(the_member.email_address, new_member=new_member, the_band=band)
        
 
def send_the_new_member_email(the_email_address, new_member, the_band):
    if not mail.is_email_valid(the_email_address):
        return False
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = 'Gig-O-Matic New Member for band {0}'.format(the_band.name)
    message.body = """
Hello! A new member has signed up for your band {0}. Please log in and
confirm the membership.

Thanks,
The Gig-O-Matic Team

    """.format(the_band.name)
    message.send()
    return True        
