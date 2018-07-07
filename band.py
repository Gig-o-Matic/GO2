#
# band class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2
from debug import *

import debug
import member
import goemail
import assoc
import gig
import plan
import json
import logging
import datetime
import stats
import json
import string
import rss
import gigoexceptions
from pytz.gae import pytz

def band_key(band_name='band_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Band', band_name)

#
# class for band
#
class Band(ndb.Model):
    """ Models a gig-o-matic band """
    name = ndb.StringProperty()
    lower_name = ndb.ComputedProperty(lambda self: self.name.lower())
    shortname = ndb.StringProperty()
    website = ndb.TextProperty()
    description = ndb.TextProperty()
    hometown = ndb.TextProperty()
    sections = ndb.KeyProperty( repeated=True ) # instrumental sections
    created = ndb.DateTimeProperty(auto_now_add=True)
#     time_zone_correction = ndb.IntegerProperty(default=0) # NO LONGER IN USE
    # new, real timezone stuff
    timezone = ndb.StringProperty()
    thumbnail_img = ndb.TextProperty(default=None)
    images = ndb.TextProperty(repeated=True)
    member_links = ndb.TextProperty(default=None)
    share_gigs = ndb.BooleanProperty(default=True)
    anyone_can_manage_gigs = ndb.BooleanProperty(default=True)
    anyone_can_create_gigs = ndb.BooleanProperty(default=True)
    condensed_name = ndb.ComputedProperty(lambda self: ''.join(ch for ch in self.name if ch.isalnum()).lower())
    simple_planning = ndb.BooleanProperty(default=False)
    plan_feedback = ndb.TextProperty()
    show_in_nav = ndb.BooleanProperty(default=True)
    send_updates_by_default = ndb.BooleanProperty(default=True)
    rss_feed = ndb.BooleanProperty(default=False)


    @classmethod
    def lquery(cls, *args, **kwargs):
        if debug.DEBUG:
            print('{0} query'.format(cls.__name__))
        return cls.query(*args, **kwargs)

def new_band(name):
    """ Make and return a new band """
    the_band = Band(parent=band_key(), name=name)
    the_band.timezone = 'UTC' # every band needs this - when creating from application, done in the UI code, but should not be None
    the_band.put()
    return the_band

def forget_band_from_key(the_band_key):
    # delete all assocs
    the_assoc_keys = assoc.get_assocs_of_band_key(the_band_key, confirmed_only=False, keys_only=True)
    ndb.delete_multi(the_assoc_keys)
    
    # delete the sections
    the_section_keys = get_section_keys_of_band_key(the_band_key)
    ndb.delete_multi(the_section_keys)

    # delete the gigs
    the_gigs = gig.get_gigs_for_band_keys(the_band_key, num=None, start_date=None)
    the_gig_keys = [a_gig.key for a_gig in the_gigs]
    
    # delete the plans
    for a_gig_key in the_gig_keys:
        plan_keys = plan.get_plans_for_gig_key(a_gig_key, keys_only = True)
        ndb.delete_multi(plan_keys)
    
    ndb.delete_multi(the_gig_keys)
    
    stats.delete_band_stats(the_band_key)
    
    # delete the band
    the_band_key.delete()

        
def get_band_from_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.lquery(Band.name==band_name, ancestor=band_key())
    band = bands_query.fetch(1)

    if len(band)==1:
        return band[0]
    else:
        return None
        
def get_band_from_condensed_name(band_name):
    """ Return a Band object by name"""
    bands_query = Band.lquery(Band.condensed_name==band_name.lower(), ancestor=band_key())
    band = bands_query.fetch(1)

    if len(band)==1:
        return band[0]
    else:
        return None

def get_band_from_key(key):
    """ Return band objects by key"""
    return key.get()

def get_band_from_id(id):
    """ Return band object by id"""

    return Band.get_by_id(int(id), parent=band_key()) # todo more efficient if we use the band because it's the parent?
    
def get_all_bands(keys_only=False):
    """ Return all objects"""
    bands_query = Band.lquery(ancestor=band_key()).order(Band.lower_name)
    all_bands = bands_query.fetch(keys_only=keys_only)
    return all_bands

def get_section_keys_of_band_key(the_band_key):
    return the_band_key.get().sections

def get_assocs_of_band_key_by_section_key(the_band_key, include_occasional=True):
    the_band = the_band_key.get()
    the_info=[]
    the_map={}
    count=0
    for s in the_band.sections:
        the_info.append([s,[]])
        the_map[s]=count
        count=count+1
    the_info.append([None,[]]) # for 'None'
    the_map[None]=count

    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band_key, include_occasional=include_occasional)
    
    for an_assoc in the_assocs:
        the_info[the_map[an_assoc.default_section]][1].append(an_assoc)

    if the_info[the_map[None]][1] == []:
        the_info.pop(the_map[None])

    return the_info

    
def new_section_for_band(the_band, the_section_name):
    the_section = Section(parent=the_band.key, name=the_section_name)
    the_section.put()

    if the_band.sections:
        if the_section not in the_band.sections:
            the_band.sections.append(the_section.key)
    else:
        the_band.sections=[the_section.key]
    the_band.put()

    return the_section

def delete_section_key(the_section_key):
    #todo make sure the section is empty before deleting it

    # get the parent band's list of sections and delete ourselves
    the_band=the_section_key.parent().get()
    if the_section_key in the_band.sections:
        i=the_band.sections.index(the_section_key)
        the_band.sections.pop(i)
        the_band.put()
    the_section_key.delete()
    
    # todo The app doesn't let you delete a section unless it's empty. But for any gig,
    # it's possible that the user has previously specified that he wants to play in the
    # section to be deleted. So, find plans with the section set, and reset the section
    # for that plan back to None to use the default.
    plan.remove_section_from_plans(the_section_key)

def get_feedback_strings(the_band):
    return the_band.plan_feedback.split('\n')

#
# class for section
#
class Section(ndb.Model):
    """ Models an instrument section in a band """
    name = ndb.StringProperty()


def set_section_indices(the_band):
    """ for every assoc in the band, set the default_section_index according to the section list in the band """

    map = {}
    for i,s in enumerate(the_band.sections):
        map[s] = i
    map[None] = None

    the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band.key, include_occasional=True)
    for a in the_assocs:
        a.default_section_index = map[a.default_section]

    ndb.put_multi(the_assocs)

#
#
# Handlers
#
#

class InfoPage(BaseHandler):
    """ class to produce the band info page """

#     @user_required
    def get(self, *args, **kwargs):    
        """ make the band info page """
        
        if 'band_name' in kwargs:
            band_name = kwargs['band_name']
            the_band = get_band_from_condensed_name(band_name)
            if the_band:
                self._make_page(None, the_band)
            else:
                return self.redirect('/')            
        else:
            if self.user:
                self._make_page(the_user=self.user)
            else:
                return self.redirect('/')            

    def _make_page(self,the_user,the_band=None):
        """ produce the info page """
        
        # find the band we're interested in
        if the_band is None:
            band_key_str=self.request.get("bk", None)
            if band_key_str is None:
                self.response.write('no band key passed in!')
                return # todo figure out what to do if there's no ID passed in
            the_band_key=ndb.Key(urlsafe=band_key_str)
            the_band=the_band_key.get()

        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
            
        if the_user is None:
            the_user_is_associated = False
            the_user_is_confirmed = False
            the_user_admin_status = False
            the_user_is_superuser = False
        else:
            the_user_is_associated = assoc.get_associated_status_for_member_for_band_key(the_user, the_band_key)
            the_user_is_confirmed = assoc.get_confirmed_status_for_member_for_band_key(the_user, the_band_key)
            the_user_admin_status = assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key)   
            the_user_is_superuser = member.member_is_superuser(the_user)

        if the_user_admin_status or the_user_is_superuser:
            the_pending = assoc.get_pending_members_from_band_key(the_band_key)
            the_invited_assocs = assoc.get_invited_member_assocs_from_band_key(the_band_key)
            the_invited=[(x.key, x.member.get().name) for x in the_invited_assocs]
        else:
            the_pending = []
            the_invited = []

        member_links=None
        if the_band.member_links:
            member_links=[]
            link_list = the_band.member_links.split('\n')
            for l in link_list:
                link_info = l.split(':',1)
                if len(link_info)==2:
                    member_links.append([link_info[0].strip(), link_info[1].strip()])

        template_args = {
            'the_band' : the_band,
            'the_user_is_associated' : the_user_is_associated,
            'the_user_is_confirmed' : the_user_is_confirmed,
            'the_user_is_band_admin' : the_user_admin_status,
            'the_pending_members' : the_pending,
            'the_invited_members' : the_invited,
            'the_member_links' : member_links,
            'num_sections' : len(the_band.sections)

        }
        self.render_template('band_info.html', template_args)

        # todo make sure the admin is really there
        
class EditPage(BaseHandler):

    @user_required
    def get(self):
        self.make_page(the_user=self.user)

    def make_page(self, the_user):

        # make sure I'm an admin or a superuser
        the_user_is_superuser = member.member_is_superuser(the_user)

        if self.request.get("new",None) is not None:
            #  creating a new band
            if not the_user_is_superuser:
                return self.redirect('/')
            the_band=None
            is_new=True
        else:
            is_new=False
            the_band_key_str=self.request.get("bk",'0')

            if the_band_key_str=='0':
                return
            else:
                the_band_key=ndb.Key(urlsafe=the_band_key_str)
            
                the_user_admin_status = assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key)   
                if not the_user_admin_status and not the_user_is_superuser:
                    return self.redirect('/')

                the_band = the_band_key.get()
                if the_band is None:
                    self.response.write('did not find a band!')
                    return # todo figure out what to do if we didn't find it

        template_args = {
            'the_band' : the_band,
            'timezones' : pytz.common_timezones,
            'newmember_is_active' : is_new,
            'is_new' : is_new
        }
        self.render_template('band_edit.html', template_args)
                    
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""

        the_user = self.user

        the_band_key=self.request.get("bk",'0')
        
        if the_band_key=='0':
            # it's a new band
            the_band=new_band('tmp')
        else:
            the_band=ndb.Key(urlsafe=the_band_key).get()
            
        if the_band is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
       
        band_name=self.request.get("band_name",None)
        if band_name is not None and band_name != '':
            the_band.name=band_name
                
        band_shortname=self.request.get("band_shortname",None)
        if band_shortname is not None:
            the_band.shortname=band_shortname
                
        website=self.request.get("band_website",None)
        if website[0:7]=='http://':
            the_band.website = website[7:]
        else:
            the_band.website = website

        the_band.thumbnail_img=self.request.get("band_thumbnail",None)
        
        image_blob = self.request.get("band_images",None)
        image_split = image_blob.split("\n")
        image_urls=[]
        for iu in image_split:
            the_iu=iu.strip()
            if the_iu:
                image_urls.append(the_iu)
        the_band.images=image_urls
        
        member_links_blob = self.request.get("band_member_links",None)
        if member_links_blob is not None:
            the_band.member_links=member_links_blob

        the_band.hometown=self.request.get("band_hometown",None)

        the_band.description=self.request.get("band_description",None)
            
        create_gigs=self.request.get("band_anyonecancreategigs",None)
        if (create_gigs):
            the_band.anyone_can_create_gigs = True
        else:
            the_band.anyone_can_create_gigs = False

        manage_gigs=self.request.get("band_anyonecanmanagegigs",None)
        if (manage_gigs):
            the_band.anyone_can_manage_gigs = True
        else:
            the_band.anyone_can_manage_gigs = False

        share_gigs=self.request.get("band_sharegigs",None)
        if (share_gigs):
            the_band.share_gigs = True
        else:
            the_band.share_gigs = False
            
        send_updates_by_default=self.request.get("band_sendupdatesbydefault",None)
        if (send_updates_by_default):
            the_band.send_updates_by_default = True
        else:
            the_band.send_updates_by_default = False
            
        rss_change = False
        enable_rss=self.request.get("band_enablerss",None)
        if (enable_rss):
            the_band.rss_feed = True
            rss_change = True
        else:
            the_band.rss_feed = False

        simple_plan=self.request.get("band_simpleplan",None)
        if (simple_plan):
            the_band.simple_planning = True
        else:
            the_band.simple_planning = False

        plan_feedback=self.request.get("band_feedback",None)
        if (plan_feedback is not None):
            the_band.plan_feedback=plan_feedback

        band_timezone=self.request.get("band_timezone",None)
        if band_timezone is not None and band_timezone != '':
            the_band.timezone=band_timezone

        the_band.put()            

        if rss_change:
            rss.make_rss_feed_for_band(the_band)

        return self.redirect('/band_info.html?bk={0}'.format(the_band.key.urlsafe()))
        


class InvitePage(BaseHandler):

    @user_required
    def get(self):
        self.make_page(the_user=self.user)

    def make_page(self, the_user):

        the_band_key_url=self.request.get("bk",None)
        if the_band_key_url is None:
            return
        else:
            the_band_key = ndb.Key(urlsafe=the_band_key_url)
            the_band = the_band_key.get()
            if the_band is None:
                self.response.write('did not find a band!')
                return # todo figure out what to do if we didn't find it

        if not assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key) and not the_user.is_superuser:
            return self.redirect('/band_info.html?bk={0}'.format(the_band.key.urlsafe()))

        template_args = {
            'the_band' : the_band
        }
        self.render_template('band_invite.html', template_args)
                    
    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""

        the_user = self.user

        the_band_key_url=self.request.get("bk",None)
        if the_band_key_url is None:
            self.response.write('did not find a band!')
            return # todo figure out what to do if we didn't find it
       
        the_band_key=ndb.Key(urlsafe=the_band_key_url)
        if not assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key) and not the_user.is_superuser:  
            return self.redirect('/band_info.html?bk={0}'.format(the_band.key.urlsafe()))

        return self.redirect('/band_info.html?bk={0}'.format(the_band.key.urlsafe()))

class DeleteBand(BaseHandler):
    """ completely delete band """
    
    @user_required
    def get(self):
        """ post handler - wants a bk """
        
        the_band_keyurl=self.request.get('bk','0')

        if the_band_keyurl=='0':
            return # todo figure out what to do

        the_band_key=ndb.Key(urlsafe=the_band_keyurl)
        
        the_user = self.user # todo - make sure the user is a superuser
        if (the_user.is_superuser):
            forget_band_from_key(the_band_key)

        return self.redirect('/band_admin.html')
        
class BandGetMembers(BaseHandler):
    """ returns the members related to a band """                   

    def post(self):    
        """ return the members for a band """
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do
            
        the_band_key = ndb.Key(urlsafe=the_band_key_str)

        assocs = assoc.get_assocs_of_band_key(the_band_key=the_band_key, confirmed_only=True)
        the_members = ndb.get_multi([a.member for a in assocs])
        
        the_members = sorted(the_members,key=lambda member: member.lower_name)
        # now sort the assocs to be in the same order as the member list
        assocs = sorted(assocs,key=lambda a: [m.key for m in the_members].index(a.member))
        
        assoc_info=[]
        the_user_is_band_admin = False
        for i in range(0,len(assocs)):
            a=assocs[i]
            m=the_members[i]
            if a.default_section:
                s = a.default_section.get().name
            else:
                s = None

            assoc_info.append( {'name':(m.nickname if m.nickname else m.name), 
                                'is_confirmed':a.is_confirmed, 
                                'is_band_admin':a.is_band_admin, 
                                'is_occasional':a.is_occasional,
                                'member_key':a.member, 
                                'section':s, 
                                'is_multisectional':a.is_multisectional, 
                                'assoc':a} )
            if a.member == the_user.key:
                the_user_is_band_admin = a.is_band_admin
                        
        the_section_keys = the_band_key.get().sections
        the_sections = ndb.get_multi(the_section_keys)

        template_args = {
            'the_band_key' : the_band_key,
            'the_assocs' : assoc_info,
            'the_sections' : the_sections,
            'the_user_is_band_admin' : the_user_is_band_admin,
        }
        self.render_template('band_members.html', template_args)

class BandGetSections(BaseHandler):
    """ returns the sections related to a band """                   

    def post(self):    
        """ return the sections for a band """
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do

        the_band_key = ndb.Key(urlsafe=the_band_key_str)
        the_band = the_band_key.get()

        the_section_index_str=self.request.get('ski',None)
        if the_section_index_str is None:
            the_section is None
        else:
            if the_section_index_str == 'None':
                the_section = None
                the_section_key = None
            else:
                the_section_key = the_band.sections[int(the_section_index_str)]
                the_section = the_section_key.get()

        the_assocs = assoc.get_assocs_of_band_key_for_section_key(the_band_key, the_section_key)

        if the_section is None and len(the_assocs)==0:
            self.response.write("None")
            return

        member_keys = [a.member for a in the_assocs]
        the_members=ndb.get_multi(member_keys)

        # make sure members and assocs are in the right order
        the_members = sorted(the_members, key=lambda m: member_keys.index(m.key))

        # someone_is_new = False
        # lately = datetime.datetime.now() - datetime.timedelta(days=4)
        # for a_section in the_members_by_section:
        #     if a_section[1]:
        #         for a in a_section[1]:
        #             if a.created and a.created > lately:
        #                 a.is_new=True
        #                 someone_is_new = True
        someone_is_new = False

        the_user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key)
                
        template_args = {
            'the_band' : the_band,
            'the_section' : the_section,
            'the_assocs' : the_assocs,
            'the_members' : the_members,
            'has_sections' : the_band.sections and len(the_band.sections) > 0,
            'the_user_is_band_admin' : the_user_is_band_admin,
            'someone_is_new' : someone_is_new
        }

        self.render_template('band_sections.html', template_args)

class SetupSections(BaseHandler):
    """ edit sections - add them, rename them, reorder them """

    @user_required
    def get(self):
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do
            
        the_band_key = ndb.Key(urlsafe=the_band_key_str)

        if not is_authorized_to_edit_band(the_band_key,the_user):
            return        

        the_band = the_band_key.get()
        the_sections = ndb.get_multi(the_band.sections)


        the_info = []
        for s in the_sections:
            the_name = string.replace(string.replace(s.name,"'",""),'"','') # ugly: disallow quotes
            the_info.append([the_name, s.key.urlsafe(), the_name])

        template_args = {
            'the_band' : the_band,
            'the_info' : json.dumps(the_info)
        }
        self.render_template('band_setup_sections.html', template_args)

    def post(self):
        the_user = self.user

        the_band_key_str=self.request.get('bk','0')
        
        if the_band_key_str=='0':
            return # todo figure out what to do
            
        the_band_key = ndb.Key(urlsafe=the_band_key_str)

        if not is_authorized_to_edit_band(the_band_key,the_user):
            return        

        the_band = the_band_key.get()

        the_section_info = self.request.get('sectionInfo', None)
        if the_section_info is None:
            return

        new_sections = json.loads(the_section_info)

        # build a new list of sections. Make sure the sections are actually in the band.
        new_section_list = []
        for n in new_sections:
            if n[1] == "":
                # this is a new section
                ns = Section(parent=the_band.key, name=string.replace(string.replace(n[0],"'",""),'"',''))
                ns.put()
                s = ns.key
            else:
                s = ndb.Key(urlsafe=n[1])
                old_section = s.get()
                if old_section.name != n[0]:
                    old_section.name=string.replace(string.replace(n[0],"'",""),'"','')
                    old_section.put()

            new_section_list.append(s)

        the_band.sections = new_section_list
        the_band.put()

        deleted_section_info = self.request.get('deletedSections', None)

        if deleted_section_info:
            the_deleted_sections = json.loads(deleted_section_info)
            if the_deleted_sections:
                assoc_keys = []
                dels = [ndb.Key(urlsafe=x) for x in the_deleted_sections]
                for d in dels:
                    assoc_keys += assoc.get_assocs_for_section_key(d, keys_only=True)

                if assoc_keys:
                    assocs = ndb.get_multi(assoc_keys)
                    for a in assocs:
                        a.default_section = None
                    ndb.put_multi(assocs)
                ndb.delete_multi(dels)

        set_section_indices(the_band)

        return


class ConfirmMember(BaseHandler):
    """ move a member from pending to 'real' member """
    
    @user_required
    def get(self):
        """ handles the 'confirm member' button in the band info page """
        
        the_user = self.user

        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')
        
        if the_member_keyurl=='0' or the_band_keyurl=='0':
            return # todo what to do?
            
        the_member_key=ndb.Key(urlsafe=the_member_keyurl)
        the_band_key=ndb.Key(urlsafe=the_band_keyurl)

        if not is_authorized_to_edit_band(the_band_key,the_user):
            return                
                    
        the_member = the_member_key.get()
        assoc.confirm_member_for_band_key(the_member, the_band_key)
        # if the user happens to be logged in, invalidate his cached list of bands and
        # bands for which he can edit gigs
        the_member.invalidate_member_bandlists(self, the_member_key)

        the_band = the_band_key.get()
        goemail.send_band_accepted_email(the_member.email_address, the_band)

        return self.redirect('/band_info.html?bk={0}'.format(the_band_keyurl))
        
class AdminMember(BaseHandler):
    """ grant or revoke admin rights """
    
    @user_required
    def post(self):
        """ post handler - wants a member key and a band key, and a flag """
        
        the_user = self.user

        the_assoc_keyurl=self.request.get('ak','0')
        the_do=self.request.get('do',None)

        if the_assoc_keyurl=='0' or the_do is None:
            return # todo figure out what to do

        the_assoc = ndb.Key(urlsafe=the_assoc_keyurl).get()

        if not is_authorized_to_edit_band(the_assoc.band,the_user):
            return                

        the_assoc.is_band_admin = (the_do=='true')
        the_assoc.put()
        
        # if the user happens to be logged in, invalidate his cached list of bands and
        # bands for which he can edit gigs
        the_assoc.member.get().invalidate_member_bandlists(self, the_assoc.member)
        
class MakeOccasionalMember(BaseHandler):
    """ grant or revoke occasional status """
    
    @user_required
    def post(self):
        """ post handler - wants a member key and a band key, and a flag """
        
        the_user = self.user

        the_assoc_keyurl=self.request.get('ak','0')
        the_do=self.request.get('do',None)

        if the_assoc_keyurl=='0' or the_do is None:
            return # todo figure out what to do

        the_assoc = ndb.Key(urlsafe=the_assoc_keyurl).get()
        
        if is_authorized_to_edit_band(the_assoc.band,the_user) or the_user.key == the_assoc.member:
            the_assoc.is_occasional = (the_do=='true')
            the_assoc.put()

class RemoveMember(BaseHandler):
    """ user quits band """
    
    @user_required
    def get(self):
        """ post handler - wants an ak """
        
        the_user = self.user

        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')

        if the_member_keyurl=='0' or the_band_keyurl=='0':
            return # todo figure out what to do

        the_member_key = ndb.Key(urlsafe=the_member_keyurl)
        the_band_key = ndb.Key(urlsafe=the_band_keyurl)
        
        if not is_authorized_to_edit_band(the_band_key,the_user):
            return                
        
        # find the association between band and member
        the_assoc=assoc.get_assoc_for_band_key_and_member_key(the_member_key, the_band_key)
        assoc.delete_association_from_key(the_assoc.key)
        gig.reset_gigs_for_contact_key(the_member_key, the_band_key)

        return self.redirect('/band_info.html?bk={0}'.format(the_band_keyurl))

class AdminPage(BaseHandler):
    """ Page for band administration """

    @user_required
    def get(self):    
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
                
    def _make_page(self,the_user):
    
        # todo make sure the user is a superuser
        
        the_bands = get_all_bands()
        
        template_args = {
            'the_bands' : the_bands,
        }
        self.render_template('band_admin.html', template_args)

class GigArchivePage(BaseHandler):
    """ Show complete gig archives """

    @user_required
    def get(self):
        self.make_page(the_user=self.user)

    def make_page(self, the_user):


        the_band_key_url=self.request.get("bk",None)
        if the_band_key_url is None:
            raise gigoexceptions.GigoException('no band key passed to GigArchivePage handler')
        else:
            the_band_key = ndb.Key(urlsafe=the_band_key_url)
        
        # make sure this member is actually in the band
        if assoc.confirm_user_is_member(the_user.key, the_band_key) is None and the_user.is_superuser is not True:
            raise gigoexceptions.GigoException('user called GigArchivePage handler but is not member')

        the_band = the_band_key.get()
        if the_band is None:
            raise gigoexceptions.GigoException('GigArchivePage handler called without a band')

        the_gigs = gig.get_gigs_for_band_keys(the_band_key, show_past=True)
        

        template_args = {
            'the_user' : the_user,
            'the_band' : the_band,
            'the_gigs' : the_gigs,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('band_gig_archive.html', template_args)

class GigTrashcanPage(BaseHandler):
    """ Show complete gig archives """

    @user_required
    def get(self):
        self.make_page(the_user=self.user)

    def make_page(self, the_user):
        the_band_key_url=self.request.get("bk",None)
        if the_band_key_url is None:
            raise gigoexceptions.GigoException('no band key passed to GigTrashcanPage handler')
        else:
            the_band_key = ndb.Key(urlsafe=the_band_key_url)
        
        # make sure this member is actually a band admin
        if not assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key) and not the_user.is_superuser:
            raise gigoexceptions.GigoException('user called GigTrashcanPage handler but is not admin')

        the_band = the_band_key.get()
        if the_band is None:
            raise gigoexceptions.GigoException('GigTrashcanPage handler calledd without a band')

        the_gigs = gig.get_trashed_gigs_for_band_key(the_band_key)

        template_args = {
            'the_user' : the_user,
            'the_band' : the_band,
            'the_gigs' : the_gigs,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('band_gig_trashcan.html', template_args)        

class GetMemberList(BaseHandler):
    """ service function to return a list of member names """

    def post(self):
        the_band_keyurl=self.request.get('bk','0')

        response_val = []
        if the_band_keyurl=='0':
            pass
        else:
            the_band_key = ndb.Key(urlsafe=the_band_keyurl)
            the_member_keys = assoc.get_member_keys_of_band_key(the_band_key)
            response_val = [ [x.get().name, x.urlsafe()] for x in the_member_keys ]
            
        self.response.write(json.dumps(response_val))


class BandNavPage(BaseHandler):

    @user_required
    def get(self):
        self.make_page(the_user=self.user)

    def make_page(self, the_user):
        the_bands = get_all_bands()
    
        template_args = {
            'the_bands' : the_bands,
        }
        self.render_template('band_nav.html', template_args)

class GetUpcoming(BaseHandler):

    def post(self):
        the_band_keyurl=self.request.get('bk','0')

        if the_band_keyurl=='0':
            return # todo figure out what to do

        the_band_key = ndb.Key(urlsafe=the_band_keyurl)

        today_date = datetime.datetime.now()
        the_gigs = gig.get_gigs_for_band_keys(the_band_key, start_date=today_date)
        
        the_gigs = [g for g in the_gigs if g.is_confirmed and not g.is_private]
        
        template_args = {
            'the_gigs' : the_gigs,
        }
        self.render_template('band_upcoming.html', template_args)

class GetPublicMembers(BaseHandler):

    def post(self):
        the_band_keyurl=self.request.get('bk','0')

        if the_band_keyurl=='0':
            return # todo figure out what to do

        the_band_key = ndb.Key(urlsafe=the_band_keyurl)

        the_member_keys = assoc.get_member_keys_of_band_key(the_band_key)
        the_members = ndb.get_multi(the_member_keys)
        the_public_members = [x for x in the_members if x.preferences and x.preferences.share_profile and x.verified]        
        
        template_args = {
            'the_members' : the_public_members
        }
        self.render_template('band_public_members.html', template_args)


class SendInvites(BaseHandler):

    def post(self):
        the_user = self.user
        the_band_keyurl=self.request.get('bk','0')

        if the_band_keyurl=='0':
            return # todo figure out what to do

        the_band_key = ndb.Key(urlsafe=the_band_keyurl)
        the_band = the_band_key.get()

        out=''
        if not assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key) and not the_user.is_superuser:
            out='not admin'
                    
        the_email_blob = self.request.get('e','')    

        # remove commas and stuff
        the_email_blob = the_email_blob.replace(',',' ')
        the_email_blob = the_email_blob.replace('\n',' ')
        the_emails = the_email_blob.split(' ')
        
        ok_email = []
        not_ok_email = []
        for e in the_emails:
            if e:
                e=e.lower()
                if goemail.validate_email(e):
                    ok_email.append(e)
                else:
                    not_ok_email.append(e)
                    
        # ok, now we have a list of good email addresses (or, at least, well-formed email addresses
        # for each one, create a new member (if there isn't one already)
        for e in ok_email:
            existing_member = member.get_member_from_email(e)
            # logging.info("existing_member:{0}".format(existing_member))

            if existing_member:
                # make sure this person isn't already a member of this band; if not, send invite
                if not assoc.get_associated_status_for_member_for_band_key(existing_member, the_band_key):
                    # create assoc for this member - they're already on the gig-o
                    # send email letting them know they're in the band
                    assoc.new_association(existing_member, the_band, confirm=True)
                    goemail.send_new_band_via_invite_email(the_band, existing_member)
            else:
                # create assoc for this member - but because they're not verified, will just show up as 'invited'
                # logging.info("creating new member")
                user_data = member.create_new_member(email=e, name='', password='invited')
                # logging.info("creating new member: {0}".format(user_data))
                the_user = user_data[1]
                if the_user:
                    assoc.new_association(the_user, the_band, confirm=True, invited=True)
                    # send email inviting them to the gig-o
                    token = self.user_model.create_invite_token(the_user.get_id())
                    verification_url = self.uri_for('inviteverification', type='i', user_id=the_user.get_id(),
                        signup_token=token, _full=True)  
                        
                    goemail.send_gigo_invite_email(the_band, the_user, verification_url)                

                    # set the new users's locale to be the same as mine by default.
                    if the_user.preferences.locale != self.user.preferences.locale:
                        the_user.preferences.locale = self.user.preferences.locale
                        the_user.put()
                else:
                    logging.error("Tried to create new invited member, but failed!")
                
        template_args = {
            'the_band_keyurl' : the_band_keyurl,
            'the_ok' : ok_email,
            'the_not_ok' : not_ok_email
        }
        self.render_template('band_invite_result.html', template_args)

class MemberSpreadsheet(BaseHandler):

    def get(self):
        the_user = self.user
        the_band_keyurl=self.request.get('bk','0')

        the_band_key = ndb.Key(urlsafe=the_band_keyurl)

        if not is_authorized_to_edit_band(the_band_key, the_user):
            return

        self.response.headers['Content-Type'] = 'application/x-gzip'
        self.response.headers['Content-Disposition'] = 'attachment; filename=members.csv'
        
        the_assocs = assoc.get_assocs_of_band_key(the_band_key)

        the_member_keys = [a.member for a in the_assocs]
        the_members = ndb.get_multi(the_member_keys)

        section_keys = get_section_keys_of_band_key(the_band_key)
        sections = ndb.get_multi(section_keys)

        section_map={}
        for s in sections:
            section_map[s.key] = s.name

        member_section_map={}
        for a in the_assocs:
            if a.default_section:
                member_section_map[a.member] = section_map[a.default_section]
            else:
                member_section_map[a.member] = ''


        data="name,nickname,email,phone,section"
        for m in the_members:
            nick = m.nickname
            if m.nickname is None:
                nick=''
            
            sec = member_section_map[m.key]

            data=u"{0}\n{1},{2},{3},{4},{5}".format(data,m.name,nick,m.email_address,m.phone,sec)

        self.response.write(data)


class ArchiveSpreadsheet(BaseHandler):

    def get(self):
        the_user = self.user
        the_band_keyurl=self.request.get('bk','0')

        the_band_key = ndb.Key(urlsafe=the_band_keyurl)

        if not is_authorized_to_edit_band(the_band_key, the_user):
            return

        self.response.headers['Content-Type'] = 'application/x-gzip'
        self.response.headers['Content-Disposition'] = 'attachment; filename=archive.csv'
        
        the_band_key_url=self.request.get("bk",None)
        if the_band_key_url is None:
            raise gigoexceptions.GigoException('no band key passed to GigArchivePage handler')
        else:
            the_band_key = ndb.Key(urlsafe=the_band_key_url)
        
        # make sure this member is actually in the band
        if assoc.confirm_user_is_member(the_user.key, the_band_key) is None and the_user.is_superuser is not True:
            raise gigoexceptions.GigoException('user called GigArchivePage handler but is not member')

        the_band = the_band_key.get()
        if the_band is None:
            raise gigoexceptions.GigoException('GigArchivePage handler called without a band')

        the_gigs = gig.get_gigs_for_band_keys(the_band_key, show_past=True)

        data="date,name,status,committed,pay"
        for g in the_gigs:
            plans = plan.get_plans_for_gig_key(g.key)
            num=len([p for p in plans if p.value in [1,2]])
            stat=0
            if (g.status and g.status in [0,1,2]):
                stat = g.status
            data=u"{0}\n{1},\"{2}\",{3},{4},\"{5}\"".format(data, member.format_date_for_member(the_user, g.date, 'short'),g.title,gig.Gig.status_names[stat],num,g.paid)

        self.response.write(data)


def is_authorized_to_edit_band(the_band_key, the_user):
    if assoc.get_admin_status_for_member_for_band_key(the_user, the_band_key) or the_user.is_superuser:
        return True
    else:
        logging.error("Non-authorized user tried to access admin function - user key {0}".format(the_user.key.urlsafe()))
        return False
        



