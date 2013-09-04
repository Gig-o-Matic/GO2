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
    name = ndb.StringProperty()
    nickname = ndb.StringProperty()
    email = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    phone = ndb.StringProperty(indexed=False)
    statement = ndb.TextProperty()
    role = ndb.IntegerProperty() # 0=vanilla member, 1=admin

def new_member(name="", email="", nickname="", phone="", statement="", role=0):
    """ make and return a new member """
    the_member = Member(parent=member_key(), name=name,\
                        email=email, nickname=nickname, phone=phone, statement=statement,\
                        role=role)
    the_member.put()
    debug_print('new_member: added member {0} with id {1}'.format(the_member.name,
                                                    the_member.key.id()))
    return the_member

def get_member_from_nickname(nickname):
    """ Return a Member object by nickname"""
    members_query = Member.query(Member.nickname==nickname, ancestor=member_key())
    member = members_query.fetch(1)
    debug_print('get_member_from_nickname: found {0} member for nickname {1}'.format(len(member),nickname))
    if len(member)==1:
        the_member = member[0]
    else:
        the_member = None
    return the_member

def get_member_from_urlsafe_key(urlsafe):
    """take a urlsafe key and cause an ancestor query to happen, to assure previous writes are committed"""
    untrusted_member=ndb.Key(urlsafe=urlsafe).get()
    return get_member_from_nickname(untrusted_member.nickname)

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
    debug_print('get_bands_of_member: got {0} assocs for member key id {1} ({2})'.format(len(assocs),the_member.key.id(),the_member.name))
    bands=[a.band.get() for a in assocs]
    debug_print('get_bands_of_member: found {0} bands for member {1}'.format(len(bands),the_member.name))
    return bands
    
def get_current_band(the_member):
    """return member's band; assume every member has just one band, for now"""
    bands=get_bands_of_member(the_member)
    if len(bands)>0:
        return bands[0]
    else:
        return None

def nav_info(the_user, the_member):

        if (the_member is not None):
            if the_user.nickname == the_member.nickname:
                is_me=True
            else:
                is_me=False
        else:
            is_me=False
            
        if member_is_admin(the_user):
            is_admin=True
        else:
            is_admin=False
            
        return { 'the_user': the_user,
                 'is_me': is_me,
                 'is_admin': is_admin,
                 'logout_link': users.create_logout_url('/') }

def member_is_admin(the_member):
    return the_member.role==1

class InfoPage(webapp2.RequestHandler):
    """Page for showing information about a member"""
    def get(self):    
        the_user = users.get_current_user()
        if the_user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(the_user)
            
    def make_page(self,user):
        debug_print('IN MEMBER_INFO {0}'.format(user.nickname()))
                                
        the_user=member.get_member_from_nickname(user.nickname())                

        the_member_key=self.request.get("mk",'0')
        print 'member_key is {0}'.format(the_member_key)
        if the_member_key!='0':
            # if we've just edited this member, the database may not have invalidated the cache.
            # Therefore, use a method to get the member that uses an ancestor query.
            the_member=member.get_member_from_urlsafe_key(the_member_key)
#            the_member=ndb.Key(urlsafe=the_member_key).get()
        else:
            return # todo what to do if it's not passed in?
            
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it
        debug_print('found member object: {0}'.format(the_member.name))
        
        if the_member.nickname == user.nickname():
            is_me = True
        else:
            is_me = False
            
        # find the bands this member is associated with
        the_bands=get_bands_of_member(the_member)
        
        if the_bands is None:
            return # todo figure out what to do if there are no bands for this member
                    
        template = je.get_template('member_info.html')
        self.response.write( template.render(
            title='Member Info',
            the_user=the_user,
            the_member=the_member,
            the_bands=the_bands,
            nav_info=member.nav_info(the_user, the_member)
        ) )


class EditPage(webapp2.RequestHandler):
    def get(self):
        print 'MEMBER_EDIT GET HANDLER'
        the_user = users.get_current_user()
        if the_user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(the_user)

    def make_page(self, user):
        debug_print('IN MEMBER_EDIT {0}'.format(user.nickname()))

        the_user=member.get_member_from_nickname(user.nickname())
                
        if the_user is None:
            return # todo figure out what to do if we get this far and there's no member

        if self.request.get("new",None) is not None:
            #  creating a new member
             the_member=None
             is_new=True
        else:
            is_new=False
            the_member_key=self.request.get("mk",'0')
            print 'the_member_key is {0}'.format(the_member_key)
            if the_member_key!='0':
                the_member=ndb.Key(urlsafe=the_member_key).get()
            else:
                the_member=the_user
            if the_member is None:
                self.response.write('did not find a member!')
                return # todo figure out what to do if we didn't find it
            debug_print('found gig object: {0}'.format(the_member.name))
                    
        template = je.get_template('member_edit.html')
        self.response.write( template.render(
            title='Gig Edit',
            the_user=the_user,
            the_member=the_member,
            nav_info=member.nav_info(the_user, the_member),
            newmember_is_active=is_new
        ) )        

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'MEMBER_EDIT POST HANDLER'

        print str(self.request.arguments())

        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return;
                    


        the_member_key=self.request.get("mk",'0')
        
        if the_member_key=='0':
            # it's a new user
            the_member=new_member()
        else:
            the_member=ndb.Key(urlsafe=the_member_key).get()
            
        if the_member is None:
            self.response.write('did not find a member!')
            return # todo figure out what to do if we didn't find it
       
        member_name=self.request.get("member_name",None)
        if member_name is not None and member_name != '':
            print 'got name {0}'.format(member_name)
            the_member.name=member_name
                
        member_email=self.request.get("member_email",None)
        if member_email is not None and member_email != '':
            print 'got email {0}'.format(member_email)
            the_member.email=member_email

        member_phone=self.request.get("member_phone",None)
        if member_phone is not None and member_phone != '':
            print 'got phone {0}'.format(member_phone)
            the_member.phone=member_phone

        member_statement=self.request.get("member_statement",None)
        if member_statement is not None and member_statement != '':
            print 'got statement {0}'.format(member_statement)
            the_member.statement=member_statement

        the_member.put()            

        return self.redirect('/member_info.html?mk={0}'.format(the_member.key.urlsafe()))
