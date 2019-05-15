#
#  member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

import debug
from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models
from webapp2_extras.appengine.auth.models import Unique
from webapp2_extras import security
from webapp2_extras.i18n import gettext as _

import time

import gig
import plan
import assoc
import datetime

import logging
from babel.dates import format_date, format_datetime, format_time


def member_key(member_name='member_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('member', member_name)

class MemberPreferences(ndb.Model):
    """ class to hold user preferences """
    email_new_gig = ndb.BooleanProperty(default=True)
    hide_canceled_gigs = ndb.BooleanProperty(default=False)
    locale = ndb.TextProperty(default='en')
    share_profile = ndb.BooleanProperty(default=True)
    share_email = ndb.BooleanProperty(default=False)
    calendar_show_only_confirmed = ndb.BooleanProperty(default=True)
    calendar_show_only_committed = ndb.BooleanProperty(default=True)
    default_view = ndb.IntegerProperty(default=0) # 0 = agenda, 1 = calendar, 2 = grid
    agenda_show_time = ndb.BooleanProperty(default=False)

class MemberError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SimplePasswordValidator:
    def __init__(self, minLength):
        self.minLength = minLength
    def ensure_valid(self, password):
        if len(password) < self.minLength:
            raise MemberError(_("Password must be at least {0} characters long").format(self.minLength))

class Member(webapp2_extras.appengine.auth.models.User):
    """ Models a gig-o-matic member """
    name = ndb.StringProperty()
    lower_name = ndb.ComputedProperty(lambda self: self.name.lower())    
    nickname = ndb.StringProperty( default=None )
    email_address = ndb.TextProperty()
    phone = ndb.StringProperty(default='', indexed=False)
    statement = ndb.TextProperty(default='')
    is_superuser = ndb.BooleanProperty(default=False)
    is_betatester = ndb.BooleanProperty(default=False)
    is_band_editor = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    preferences = ndb.StructuredProperty(MemberPreferences)
    seen_motd = ndb.BooleanProperty(default=False) # deprecated
    seen_motd_time = ndb.DateTimeProperty(default=None)
    seen_welcome = ndb.BooleanProperty(default=False)
    show_long_agenda = ndb.BooleanProperty(default=True)
    pending_change_email = ndb.TextProperty(default='', indexed=False)
    images = ndb.TextProperty(repeated=True)
    display_name = ndb.ComputedProperty(lambda self: self.nickname if self.nickname else self.name)
    last_activity = ndb.DateTimeProperty(auto_now=True)
    last_calfetch = ndb.DateTimeProperty(default=None)
    local_email_address = ndb.ComputedProperty(lambda self: self.email_address)
    cal_feed_dirty = ndb.BooleanProperty(default=True)

    """Password validation class. Accepts .ensure_valid(pwd) and throws if invalid"""
    PasswordValidator = SimplePasswordValidator(minLength=5)

    @classmethod
    def lquery(cls, *args, **kwargs):
        if debug.DEBUG:
            print('{0} query'.format(cls.__name__))
        return cls.query(*args, **kwargs)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
                The raw password which will be hashed and stored
        """
        self.PasswordValidator.ensure_valid(raw_password)
        self.password = security.generate_password_hash(raw_password, length=12)

    def set_email_to_pending(self):
        """ Changes the email address for the current user"""

        new_email = self.pending_change_email.lower()
        success = False
        if new_email != '':
            success, existing = \
                Unique.create_multi(['Member.auth_id:%s'%new_email,
                                     'Member.email_address:%s'%new_email])
            if not success:
                logging.error('Unable to create user for email %s because of \
                    duplicate keys' % new_email)
            else:
                # delete the old unique values
                Unique.delete_multi(['Member.auth_id:%s'%self.email_address,
                                     'Member.email_address:%s'%self.email_address])

                self.email_address=new_email
                self.auth_ids=[new_email]
            self.pending_change_email = ''
            self.put()

        if success:
            return new_email
        else:
            return None

    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
                The user_id of the requesting user.
        :param token:
                The token string to be verified.
        :returns:
                A tuple ``(User, timestamp)``, with a user object and
                the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
                timestamp = int(time.mktime(valid_token.created.timetuple()))
                return user, timestamp

        return None, None

    @classmethod
    def create_email_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'email')
        return entity.token

    @classmethod
    def delete_email_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'email', token).delete()

    @classmethod
    def create_invite_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'invite')
        return entity.token

    @classmethod
    def delete_invite_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'invite', token).delete()

    @classmethod
    def get_band_list(cls, req, the_member_key):
        """ check to see if this is in the session - if so, just use it """
        if 'member_bandlist' in req.session.keys() and not req.member_cache_is_dirty(the_member_key):
            the_bands = req.session['member_bandlist']
        else:
            band_keys=assoc.get_band_keys_of_member_key(the_member_key, confirmed_only=True)
            the_bands = [bandkey.get() for bandkey in band_keys]

            req.session['member_bandlist'] = the_bands
        return the_bands

    @classmethod
    def get_add_gig_band_list(cls, req, the_member_key):
        """ check to see if this is in the session - if so, just use it """
        
        if hasattr(req,'session') is False:
            return []
                
        if 'member_addgigbandlist' in req.session.keys() and not req.member_cache_is_dirty(the_member_key):
            the_manage_bands = req.session['member_addgigbandlist']
        else:
            band_keys=assoc.get_band_keys_of_member_key(the_member_key, confirmed_only=True)
            the_bands = ndb.get_multi(band_keys)
            the_manage_bands = []
            for b in the_bands:
                if b.anyone_can_create_gigs or \
                    req.user.is_superuser or \
                    assoc.get_admin_status_for_member_for_band_key(req.user, b.key):
                    the_manage_bands.append(b)
            req.session['member_addgigbandlist'] = the_manage_bands
        return the_manage_bands



    @classmethod
    def invalidate_member_bandlists(cls, req, member_key):
        """ delete the bandlists from the session if they are changing """
#         req.session.pop('member_bandlist',None)
#         req.session.pop('member_addgigbandlist',None)
#         print("bandlist is {0}".format(req.session))
        req.set_member_cache_dirty(member_key)

    @classmethod
    def create_user(cls, auth_id, unique_properties=None, **user_values):
        cls.PasswordValidator.ensure_valid(user_values.get("password_raw"))
        return super(Member, cls).create_user(auth_id, unique_properties, **user_values)

def create_new_member(email, name, password):
    if name=='':
        name=email.split('@')[0]
    unique_properties = ['email_address']

    user_data = Member.create_user(email.lower(),
        unique_properties,
        email_address=email, name=name, password_raw=password,
        verified=False, preferences=MemberPreferences())
    return user_data


def member_key_from_urlsafe(urlsafe):
    return ndb.Key(urlsafe=urlsafe)


def get_member(the_member_key):
    """ takes a single member key or a list """
    if isinstance(the_member_key, list):
        return ndb.get_multi(the_member_key)
    else:
        if not isinstance(the_member_key, ndb.Key):
            raise TypeError("get_member expects a member key")
        return the_member_key.get()


def rewrite_all_members():
    members = get_all_members()
    ndb.put_multi(members)


def get_all_members(order=True, keys_only=False, verified_only=False, pagelen=0, page=0):
    """ Return all member objects """

    args=[]
    if verified_only:
        args=[ndb.GenericProperty('verified')==True]

    if order:
        member_query = Member.lquery(*args).order(Member.lower_name)
    else:
        member_query = Member.lquery(*args)
    
    if pagelen == 0:
        members = member_query.fetch(keys_only=keys_only)
    else:
        members = member_query.fetch(keys_only=keys_only, offset=page*pagelen, limit=pagelen)

    return members

def search_for_members(order=True, keys_only=False, verified_only=False, pagelen=0, page=0, search=None):
    """ Return all member objects """

    args=[]
    if verified_only:
        args=[ndb.GenericProperty('verified')==True]

    if search:
        args.append(ndb.StringProperty('local_email_address')==search)

    # print('\n\n{0}\n\n'.format(*args))


    if order:
        member_query = Member.lquery(*args).order(Member.lower_name)
    else:
        member_query = Member.lquery(*args)
    
    if pagelen == 0:
        members = member_query.fetch(keys_only=keys_only)
    else:
        members = member_query.fetch(keys_only=keys_only, offset=page*pagelen, limit=pagelen)

    return members

def reset_motd():
    members=get_all_members()
    for m in members:
        m.seen_motd=False
    ndb.put_multi(members)

    
def forget_member_from_key(the_member_key):
    """ deletes a member, including all gig plans """

    # first find all of the assocs to bands
    the_assocs = assoc.get_assocs_of_member_key(the_member_key=the_member_key, confirmed_only=False)
    # delete all plans & abdicate as contact for gigs
    for an_assoc in the_assocs:
        plan.delete_plans_for_member_key_for_band_key(the_member_key, an_assoc.band)
        gig.reset_gigs_for_contact_key(the_member_key, an_assoc.band)

    # now quit the bands
    the_assoc_keys=[a.key for a in the_assocs]
    ndb.delete_multi(the_assoc_keys)

    # delete the old unique values
    the_member=the_member_key.get()
    if the_member:
        Unique.delete_multi(['Member.auth_id:%s'%the_member.email_address,
                             'Member.email_address:%s'%the_member.email_address])  
    # bye!    
    the_member_key.delete()
    
def get_member_from_urlsafe_key(urlsafe):
    """take a urlsafe key and cause an ancestor query to happen, to assure previous writes are committed"""
    untrusted_member=ndb.Key(urlsafe=urlsafe).get()
    return get_member_from_nickname(untrusted_member.nickname)


def get_member(the_member_key):
    """ takes a single member key or a list """
    if isinstance(the_member_key, list):
        return ndb.get_multi(the_member_key)
    else:
        if not isinstance(the_member_key, ndb.Key):
            raise TypeError("get_member expects a member key")
        return the_member_key.get()


def get_member_from_email(the_email, keys_only=False):
    """ Return member object from email address """
    member = Member.get_by_auth_id(the_email)
    return member

def member_count_bands(the_member_key):
    return len(assoc.get_assocs_of_member_key(the_member_key, confirmed_only=True, keys_only=True))

def member_is_superuser(the_member):
    return the_member.is_superuser

def set_seen_motd_for_member_key(the_member_key):
    the_member = the_member_key.get()
    # the_member.seen_motd = True
    the_member.seen_motd_time = datetime.datetime.now()
    the_member.put()

def set_seen_welcome_for_member_key(the_member_key):
    the_member = the_member_key.get()
    the_member.seen_welcome = True
    the_member.put()

def format_date_for_member(the_user, the_date, format="short"):
    the_locale='en'
    if the_user.preferences and the_user.preferences.locale:
        the_locale=the_user.preferences.locale
    the_str=''
    if format=='short':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="short"))
    elif format=='long':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="full"))
    elif format=='month':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="MMMM y"))
    elif format=='day':
        the_str=u'{0}'.format(format_date(the_date,locale=the_locale,format="EEE"))
    elif format=='datepicker':
        # here we want the short format but replace the year with the complete year
        the_str=format_date(the_date,locale=the_locale,format="short")

        if not the_str[-4:].isdigit(): # if we only have a 2-digit date
            the_str=the_str[:-2]+str(the_date.year)

    return the_str


def update_all_uniques():
    the_members = get_all_members(order=False)

    logging.info('starting unique cleanup')
    m_list=[]
    t_list=[]
    for m in the_members:
        ea = m.email_address.lower()
        if ea != m.email_address:
            # found an upper-case email
        
            # first, make new auth_id and email_addresses Uniques
            newauth = Unique.create('Member.auth_id:%s'%ea)
            if newauth is False:
                logging.error('Unable to create unique auth_id for email {0}'.format(ea))
        
            newemail = Unique.create('Member.email_address:%s'%ea)
            if newemail is False:
                logging.error('Unable to create unique email_address for email {0}'.format(ea))

            if newauth and newemail:            
                # delete the old unique values
                logging.info('deleting old tokens for {0}'.format(m.email_address))
                Unique.delete_multi(['Member.auth_id:%s'%m.email_address,
                                     'Member.email_address:%s'%m.email_address])
            else:
                logging.error('did not delete old tokens')

            m.email_address=ea
            m.auth_ids=[ea]
            m_list.append(m)
        else:
            # email address is fine, just make sure we have tokens for this guy
            t_list.append('Member.auth_id:%s'%ea)
            t_list.append('Member.email_address:%s'%ea)

    if m_list:
        ndb.put_multi(m_list)
        
    if t_list:
        Unique.create_multi(t_list)

    logging.info('unique cleanup done')

def clean_up_verified():
    """ find members that have not been verified for some reason """
    
    """ first, find people who have seen the welcome message but are not verified. Weird. """
#     member_query = Member.query(ndb.AND(Member.seen_welcome == True, ndb.GenericProperty('verified')==False))
# 
#     members = member_query.fetch()
#     logging.info('fixed verified for {0} members'.format(len(members)))
#     
#     for m in members:
#         m.verified = True
#     
#     ndb.put_multi(members)
    
    """ now, find any members who have made plans but are not verified. really weird. """
    member_query = Member.query(ndb.GenericProperty('verified')==False)
    members = member_query.fetch()

    set = []
    for m in members:
        plan_query = plan.Plan.lquery(plan.Plan.member==m.key)
        plans = plan_query.fetch(keys_only=True)
        if plans:
            m.verified=True
            set.append(m)
            logging.info("found an unverified with plans! {0}".format(m.name))

    if set:
        ndb.put_multi(set)
    
def lookup_member_key(request):
    the_member_keyurl = request.get("mk", '0')
    if the_member_keyurl == '0':
        raise MemberError("Couldn't find member")
    else:
        # if we've just edited this member, the database may not have
        # invalidated the cache. Therefore, use a method to get the
        # member that uses an ancestor query.
        the_member_key = ndb.Key(urlsafe=the_member_keyurl)

    if the_member_key is None:
        raise MemberError("Couldn't find member")

    return the_member_key

def make_member_cal_dirty(the_member_key):
    the_member = the_member_key.get()
    the_member.cal_feed_dirty = True
    the_member.put()


def rest_member_info(the_member, include_id=True):
    obj = { k:getattr(the_member,k) for k in ['display_name'] }
    return obj

