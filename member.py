#
# member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from debug import *

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

def get_member_from_key(key):
    """ Return member objects by key"""
    return key.get()

def get_member_from_nickname(nickname):
    """ Return a Member object by nickname"""
    members_query = Member.query(Member.nickname==nickname)
    member = members_query.fetch(1)
    debug_print('get_member_from_nickname: found {0} member for nickname {1}'.format(len(member),nickname))
    if len(member)==1:
        return member[0]
    else:
        return None
