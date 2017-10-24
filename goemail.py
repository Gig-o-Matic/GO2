import webapp2
from google.appengine.api import mail
from google.appengine.api import users

import gig
import member
import assoc
import logging
import re
import pickle
import os

from webapp2_extras import i18n
from webapp2_extras.i18n import gettext as _

import goannouncements

# need this for sending stuff to the superuser - can't use the decorated version
_bare_admin_email_address = 'gigomatic.superuser@gmail.com'

# The MailServiceStub class used by dev_appserver can't handle a sender address that's more
# than a raw email address, but production GAE doesn't have this limitation.
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
    _admin_email_address = 'Gig-o-matic <gigomatic.superuser@gmail.com>'
else:
    _admin_email_address = 'gigomatic.superuser@gmail.com'


def validate_email(to):
    # + and . are allowed in username, and . in the domain name, but neither can be
    # the leading character. Alphanumerics, - and _ are allowed anywhere.
    valid_address = r"^[_a-z0-9-]+((\.|\+)[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
    if (not mail.is_email_valid(to)) or (re.match(valid_address, to.lower()) is None):
        logging.error("invalid recipient address '{0}'".format(to))
        return False
    else:
        return True

def _send_admin_mail(to, subject, body, html=None, reply_to=None):

    if validate_email(to) is False:
        return False

    message = mail.EmailMessage()
    message.sender = _admin_email_address
    message.to = to
    message.subject = subject
    message.body = body
    if reply_to is not None:
        message.reply_to = reply_to
    if html is not None:
        message.html = html

    try:
        message.send()
        return True
    except Exception as e:
        logging.error("Failed to send mail {0} to {1}.\n{2}".format(subject, to, e))
        return False

def send_registration_email(the_email, the_url):

    return _send_admin_mail(the_email, _('Welcome to Gig-o-Matic'), _('welcome_msg_email').format(the_url))

def send_band_accepted_email(the_email, the_band):
    return _send_admin_mail(the_email, _('Gig-o-Matic: Confirmed!'),
                            _('member_confirmed_email').format(the_band.name, the_band.key.urlsafe()))

def send_forgot_email(the_email, the_url):
    return _send_admin_mail(the_email, _('Gig-o-Matic Password Reset'), _('forgot_password_email').format(the_url))

# send an email announcing a new gig
def send_gig_email(the_member, the_gig, the_band, the_gig_url, is_edit=False, is_reminder=False, change_string=""):

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

    # get the special URLs for "yes" and "no" answers
    the_yes_url, the_no_url, the_snooze_url = gig.get_confirm_urls(the_member, the_gig)

    reply_to = None
    if contact is not None:
       reply_to = contact.email_address
    if is_edit:
        title_string='{0} ({1})'.format(_('Gig Edit'),change_string)
    elif is_reminder:
        title_string='Gig Reminder:'
    else:
        title_string=_('New Gig:')

    the_date_string = goannouncements.format_date_string(the_gig.date, the_member)
    the_time_string = goannouncements.format_time_string(the_gig)
    the_status_string = [_('Unconfirmed'), _('Confirmed!'), _('Cancelled!')][the_gig.status]

    def format_body(body_format_str):
        return body_format_str.format(the_band.name, the_gig.title, the_date_string, the_time_string, contact_name,
                                      the_status_string, the_gig.details, the_gig_url, "", the_yes_url, the_no_url,
                                      the_snooze_url)

    if is_edit:
        body = _('edited_gig_email').format(the_band.name, the_gig.title, the_date_string, the_time_string, contact_name,
                                            the_status_string, the_gig.details, the_gig_url, change_string)
        html = None
    elif is_reminder:
        body = format_body(_('reminder_gig_email'))
        html = format_body(_('reminder_gig_email_html'))
    else:
        body = format_body(_('new_gig_email'))
        html = format_body(_('new_gig_email_html'))

    return _send_admin_mail(the_email_address, u'{0} {1}'.format(title_string, the_gig.title), body, html=html, reply_to=reply_to)

class EmailGigHandler(webapp2.RequestHandler):

    def post(self):
        the_shared_params = pickle.loads(self.request.get('the_shared_params'))
        the_member_params = pickle.loads(self.request.get('the_member_params'))

        the_member_key  = the_member_params['the_member_key']
        the_gig_key = the_shared_params['the_gig_key']
        the_band_key = the_shared_params['the_band_key']
        the_gig_url = the_shared_params['the_gig_url']
        is_edit = the_shared_params['is_edit']
        is_reminder = the_shared_params['is_reminder']
        change_string = the_shared_params['change_string']

        send_gig_email(the_member_key.get(), the_gig_key.get(), the_band_key.get(), the_gig_url, is_edit, is_reminder, change_string)

        self.response.write( 200 )

def send_new_member_email(band,new_member):
    members=assoc.get_admin_members_from_band_key(band.key)
    for the_member in members:
        send_the_new_member_email(the_member.preferences.locale, the_member.email_address, new_member=new_member, the_band=band)


def send_the_new_member_email(the_locale, the_email_address, new_member, the_band):

    i18n.get_i18n().set_locale(the_locale)

    return _send_admin_mail(the_email_address,
                            _('Gig-o-Matic New Member for band {0}').format(the_band.name),
                            _('new_member_email').format('{0} ({1})'.format(new_member.name, new_member.email_address),
                                                        the_band.name, the_band.key.urlsafe()))

def send_new_band_via_invite_email(the_band, the_member):
    return _send_admin_mail(the_member.email_address, _('Gig-o-Matic New Band Invite'),
                            _('new_band_via_invite_email').format(the_band.name))

def send_gigo_invite_email(the_band, the_member, the_url):
    return _send_admin_mail(the_member.email_address, _('Invitation to Join Gig-o-Matic'),
                            _('gigo_invite_email').format(the_band.name, the_url))

def send_the_pending_email(the_email_address, the_confirm_link):
    return _send_admin_mail(the_email_address, _('Gig-o-Matic Confirm Email Address'),
                            _('confirm_email_address_email').format(the_confirm_link))

def notify_superuser_of_archive(the_num):
    return _send_admin_mail(_bare_admin_email_address, 'Gig-o-Matic Auto-Archiver'
                           "Yo! The Gig-o-Matic archived {0} gigs last night.".format(the_num))

def notify_superuser_of_old_tokens(the_num):
    return _send_admin_mail(_bare_admin_email_address, 'Gig-o-Matic Old Tokens',
                           "Yo! The Gig-o-Matic found {0} old signup tokens last night.".format(the_num))

def send_band_request_email(the_email_address, the_name, the_info):
    if not mail.is_email_valid(the_email_address):
        return False
    body = u"""
Hi there! Someone has requested to add their band to the Gig-o-Matic. SO EXCITING!

{0}
{1}
{2}

Enjoy,
Team Gig-o-Matic

    """.format(the_email_address, the_name, the_info)
    return _send_admin_mail(_bare_admin_email_address, 'Gig-o-Matic New Band Request', body)
