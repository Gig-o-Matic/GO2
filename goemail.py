import webapp2
from google.appengine.api import mail
from google.appengine.api import users
import band
import gig
import member
import assoc
import logging

SENDER_EMAIL = 'gigomatic.superuser@gmail.com'

def send_registration_email(the_email, the_url):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = 'Welcome to Gig-O-Matic'
    message.body = u"""
Hello! You have registered to join Gig-O-Matic - click the link below to log in and you're good to go.

{0}

Thanks,
The Gig-O-Matic Team

    """.format(the_url)

    message.send()
    return True

def send_band_accepted_email(the_email, the_band):

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = 'Gig-O-Matic: Confirmed!'
    message.body = u"""
Hello! You have been confirmed as a member of {0} and can now start using Gig-O-Matic to manage your band life.

http://gig-o-matic.appspot.com/band_info.html?bk={1}

Thanks,
The Gig-O-Matic Team

    """.format(the_band.name, the_band.key.urlsafe())

    message.send()
    return True
    
    
def send_forgot_email(the_email, the_url):

    if not mail.is_email_valid(the_email):
        logging.error("send_forgot_email invalid email: {0}".format(the_email))
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = 'Gig-O-Matic Password Reset'
    message.body = u"""
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
    message.body = u"""
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
    the_members = assoc.get_member_keys_of_band_key(the_band_key)
    for the_member_key in the_members:
        the_member = the_member_key.get()
        if the_member.preferences:
            if the_member.preferences.email_new_gig:
                send_newgig_email(the_member.email_address, the_gig, the_band, the_gig_url)
        

def send_new_member_email(band,new_member):
    members=assoc.get_admin_members_from_band_key(band.key)
    for the_member in members:
        send_the_new_member_email(the_member.email_address, new_member=new_member, the_band=band)
        
 
def send_the_new_member_email(the_email_address, new_member, the_band):

    if not mail.is_email_valid(the_email_address):
        return False
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = 'Gig-O-Matic New Member for band {0}'.format(the_band.name)
    message.body = u"""
Hello! A new member {0} has signed up for your band {1}. Please log in and
confirm the membership.

http://gig-o-matic.appspot.com/band_info.html?bk={2}

Thanks,
The Gig-O-Matic Team

    """.format(new_member.name, the_band.name, the_band.key.urlsafe())
    message.send()
    return True        

def send_the_pending_email(the_email_address, the_confirm_link):
    if not mail.is_email_valid(the_email_address):
        return False
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = 'Gig-O-Matic Confirm Email Address'
    message.body = u"""
Hi there! Someone has requested to change their Gig-O-Matic ID to this email address.
If it's you, please click the link to confirm. If not, just ignore this and it will
go away.

{0}

Thanks,
Team Gig-O-Matic

    """.format(the_confirm_link)
    message.send()
    return True

def notify_superuser_of_archive(the_num):
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = 'gigomatic.superuser@gmail.com'
    message.subject = 'Gig-O-Matic Auto-Archiver'
    message.body = """
Yo! The Gig-o-Matic archived {0} gigs last night.
    """.format(the_num)
    message.send()
    return True        
