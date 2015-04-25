import webapp2
from google.appengine.api import mail
from google.appengine.api import users
import band
import gig
import member
import assoc
import logging
import re

from webapp2_extras import i18n
from webapp2_extras import jinja2
from webapp2_extras.i18n import gettext as _

SENDER_EMAIL = 'gigomatic.superuser@gmail.com'

def validate_email(the_string):
    if re.match(r"^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$",the_string):
        return True

def set_locale_for_user(the_req, the_locale_override=None):
    if the_locale_override:
        locale=the_locale_override
    else:
        if the_req.user:
            if the_req.user.preferences.locale:
                locale=the_req.user.preferences.locale
            else:
                locale='en'
        else:
            locale='en'

    i18n.get_i18n().set_locale(locale)

def send_registration_email(the_req, the_email, the_url, the_locale_override=None):

    set_locale_for_user(the_req, the_locale_override)

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = _('Welcome to Gig-o-Matic')
#     message.body = u"""
# Hello! You have registered to join Gig-o-Matic - click the link below to log in and you're good to go. (The link
# is good for 48 hours - after that you can just register again to get a new one if you need it.)
# 
# {0}
# 
# Thanks,
# The Gig-o-Matic Team
# 
#     """.format(the_url)
    message.body=_('welcome_msg_email').format(the_url)
    
    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True

def send_band_accepted_email(the_req, the_email, the_band):

    set_locale_for_user(the_req)

    if not mail.is_email_valid(the_email):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = _('Gig-o-Matic: Confirmed!')
#     message.body = u"""
# Hello! You have been confirmed as a member of {0} and can now start using Gig-o-Matic to manage your band life.
# 
# http://gig-o-matic.appspot.com/band_info.html?bk={1}
# 
# Thanks,
# The Gig-o-Matic Team
# 
#     """.format(the_band.name, the_band.key.urlsafe())
    message.body = _('member_confirmed_email').format(the_band.name, the_band.key.urlsafe())

    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True
    
def send_forgot_email(the_req, the_email, the_url):

    set_locale_for_user(the_req)

    if not mail.is_email_valid(the_email):
        logging.error("send_forgot_email invalid email: {0}".format(the_email))
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email
    message.subject = _('Gig-o-Matic Password Reset')
#     message.body = u"""
# Hello! To reset your Gig-o-Matic password, click the link below.
# 
# {0}
# 
# Thanks,
# The Gig-o-Matic Team
# 
#     """.format(the_url)

    message.body = _('forgot_password_email').format(the_url)

    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True
    
##########
#
# send an email announcing a new gig
#
##########    
def send_newgig_email(the_member, the_gig, the_band, the_gig_url, is_edit=False, change_string=""):
 
    the_locale=the_member.preferences.locale
    the_email_address = the_member.email_address
    
    if not mail.is_email_valid(the_email_address):
        return False

    i18n.get_i18n().set_locale(the_locale)
        
    contact_key=the_gig.contact
    if contact_key:
        contact = contact_key.get()
        contact_name=contact.name
    else:
        contact = None
        contact_name="??"        
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    if contact is not None:
        message.reply_to = contact.email_address
    message.to = the_email_address
    if is_edit:
        title_string='{0} ({1})'.format(_('Gig Edit'),change_string)
    else:
        title_string=_('New Gig:')
    message.subject = '{0} {1}'.format(title_string, the_gig.title)
#     message.body = u"""
# Hello! A new gig has been added to the Gig-o-Matic for your band {0}:
# 
# {1}
# Date: {2}
# Time: {3}
# Contact: {4}
# 
# {5}
# 
# Can you make it? You can (and should!) weigh in here: {6}
# 
# Thanks,
# The Gig-o-Matic Team
# 
#     """.format(the_band.name, the_gig.title, the_gig.date, the_gig.settime, contact_name, the_gig.details, the_gig_url)
    the_date_string = "{0} ({1})".format(member.format_date_for_member(the_member, the_gig.date),
                                       member.format_date_for_member(the_member, the_gig.date, "day"))

    the_time_string = ""
    if the_gig.calltime:
        the_time_string = u'{0} ({1})'.format(the_gig.calltime, _('Call Time'))
    if the_gig.settime:
        if the_time_string:
            the_time_string = u'{0}, '.format(the_time_string)
        the_time_string = u'{0}{1} ({2})'.format(the_time_string,the_gig.settime, _('Set Time'))
    if the_gig.endtime:
        if the_time_string:
            the_time_string = u'{0}, '.format(the_time_string)
        the_time_string = u'{0}{1} ({2})'.format(the_time_string,the_gig.endtime, _('End Time'))
        
    the_status_string=[_('Unconfirmed'), _('Confirmed!'), _('Cancelled!')][the_gig.status]
        
    if is_edit is False:
        message.body=_('new_gig_email').format(the_band.name, the_gig.title, the_date_string, the_time_string, contact_name, the_status_string, the_gig.details, the_gig_url)
    else:
        message.body=_('edited_gig_email').format(the_band.name, the_gig.title, the_date_string, the_time_string, contact_name, the_status_string, the_gig.details, the_gig_url, change_string)
        
    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True

def announce_new_gig(the_gig, the_gig_url, is_edit=False, change_string=""):
    the_band_key = the_gig.key.parent()
    the_band=the_band_key.get()
    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band_key, include_occasional=the_gig.invite_occasionals)
    the_members = [a.member for a in the_assocs]
    for the_member_key in the_members:
        the_member = the_member_key.get()
        if the_member.preferences:
            if the_member.preferences.email_new_gig:
                send_newgig_email(the_member, the_gig, the_band, the_gig_url, is_edit, change_string)
        

def send_new_member_email(band,new_member):
    members=assoc.get_admin_members_from_band_key(band.key)
    for the_member in members:
        send_the_new_member_email(the_member.preferences.locale, the_member.email_address, new_member=new_member, the_band=band)
        
 
def send_the_new_member_email(the_locale, the_email_address, new_member, the_band):

    if not mail.is_email_valid(the_email_address):
        return False
        
    i18n.get_i18n().set_locale(the_locale)
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = _('Gig-o-Matic New Member for band {0})').format(the_band.name)
#     message.body = u"""
# Hello! A new member {0} has signed up for your band {1}. Please log in and
# confirm the membership.
# 
# http://gig-o-matic.appspot.com/band_info.html?bk={2}
# 
# Thanks,
# The Gig-o-Matic Team
# 
#     """.format(new_member.name, the_band.name, the_band.key.urlsafe())
    message.body = _('new_member_email').format(new_member.name, the_band.name, the_band.key.urlsafe())

    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True        

def send_new_band_via_invite_email(the_req, the_band, the_member):
    set_locale_for_user(the_req, the_member.preferences.locale)
    
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_member.email_address
    message.subject = _('Gig-o-Matic New Band Invite')
    message.body = _('new_band_via_invite_email').format(the_band.name)
    try:
        message.send()
    except:
        logging.error(u'failed to send new_band_via_invite email to user {0}!'.format(the_member.email_address))

    return True

def send_gigo_invite_email(the_req, the_band, the_member, the_url):
    set_locale_for_user(the_req) # send the invite in the admin member's language
    if not mail.is_email_valid(the_member.email_address):
        return False
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_member.email_address
    message.subject = _('Invitation to Join Gig-o-Matic')
    message.body=_('gigo_invite_email').format(the_band.name, the_url)
    try:
        message.send()
    except:
        logging.error('failed to send email!')


def send_the_pending_email(the_req, the_email_address, the_confirm_link):
    if not mail.is_email_valid(the_email_address):
        return False
        
    set_locale_for_user(the_req)
        
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = the_email_address
    message.subject = _('Gig-o-Matic Confirm Email Address')
#     message.body = u"""
# Hi there! Someone has requested to change their Gig-o-Matic ID to this email address.
# If it's you, please click the link to confirm. If not, just ignore this and it will
# go away.
# 
# {0}
# 
# Thanks,
# Team Gig-o-Matic
# 
#     """.format(the_confirm_link)
    message.body=_('confirm_email_address_email').format(the_confirm_link)
    try:
        message.send()
    except:
        logging.error('failed to send email!')

    return True

def notify_superuser_of_archive(the_num):
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = 'gigomatic.superuser@gmail.com'
    message.subject = 'Gig-o-Matic Auto-Archiver'
    message.body = """
Yo! The Gig-o-Matic archived {0} gigs last night.
    """.format(the_num)
    try:
        message.send()
    except:
        logging.error('failed to send email!')
        
    return True        


def notify_superuser_of_old_tokens(the_num):
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = 'gigomatic.superuser@gmail.com'
    message.subject = 'Gig-o-Matic Old Tokens'
    message.body = """
Yo! The Gig-o-Matic found {0} old signup tokens last night.
    """.format(the_num)
    try:
        message.send()
    except:
        logging.error('failed to send email!')
    return True        

def send_band_request_email(the_email_address, the_name, the_info):
    if not mail.is_email_valid(the_email_address):
        return False
    message = mail.EmailMessage()
    message.sender = SENDER_EMAIL
    message.to = 'gigomatic.superuser@gmail.com'
    message.subject = 'Gig-o-Matic New Band Request'
    message.body = u"""
Hi there! Someone has requested to add their band to the Gig-o-Matic. SO EXCITING!

{0}
{1}
{2}

Enjoy,
Team Gig-o-Matic

    """.format(the_email_address, the_name, the_info)
    try:
        message.send()
    except:
        logging.error('failed to send email!')

    return True
