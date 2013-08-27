#
# member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.api import users
from google.appengine.ext import ndb
import webapp2
from member import *
from assoc import *
from gig import *
from jinja2env import jinja_environment as je
import debug

def member_key(member_name='member_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('member', member_name)

#
# class for member
#
class Member(ndb.Model):
    """ Models a gig-o-matic member """
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    nickname = ndb.StringProperty()
    email = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

def new_member(first_name="", last_name="", email="", nickname=""):
    """ make and return a new member """
    the_member = Member(parent=member_key(), first_name=first_name, last_name=last_name,\
                        email=email, nickname=nickname)
    the_member.put()
    debug_print('new_member: added member {0} {1} with id {2}'.format(the_member.first_name,
                                                    the_member.last_name,
                                                    the_member.key.id()))
    return the_member

def get_member_from_nickname(nickname):
    """ Return a Member object by nickname"""
    members_query = Member.query(Member.nickname==nickname)
    member = members_query.fetch(1)
    debug_print('get_member_from_nickname: found {0} member for nickname {1}'.format(len(member),nickname))
    if len(member)==1:
        the_member = member[0]
    else:
        the_member = None
    return the_member

def get_member_from_key(key):
    """ Return member objects by key"""
    return key.get()

def get_member_from_id(id):
    """ Return member object by id"""
    debug_print('get_member_from_id looking for id {0}'.format(id))
    return Member.get_by_id(int(id), parent=member_key()) # todo more efficient if we use the band because it's the parent?

def get_bands_of_member(the_member):
    """ Return band objects by member"""
    assoc_query = assoc.Assoc.query(assoc.Assoc.member==the_member.key, ancestor=assoc.assoc_key())
    assocs = assoc_query.fetch()
    debug_print('get_bands_of_member: got {0} assocs for member key id {1} ({2})'.format(len(assocs),the_member.key.id(),the_member.first_name))
    bands=[a.band.get() for a in assocs]
    debug_print('get_bands_of_member: found {0} bands for member {1}'.format(len(bands),the_member.first_name))
    return bands
    
def get_current_band(the_member):
    """return member's band; assume every member has just one band, for now"""
    bands=get_bands_of_member(the_member)
    if len(bands)>0:
        return bands[0]
    else:
        return None

class InfoPage(webapp2.RequestHandler):

    def get(self):    
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)
            
    def make_page(self,user):
        debug_print('IN AGENDA {0}'.format(user.nickname()))
        
        member=get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if member is None:
            return # todo figure out what to do if we get this far and there's no member
            
        # find the bands this member is associated with
        bands=get_bands_of_member(member)
        
        if bands is None:
            return # todo figure out what to do if there are no bands for this member
                    
        template = je.get_template('member_info.html')
        self.response.write( template.render(
            title='Member Info',
            member=member,
            bands=bands
        ) )        
