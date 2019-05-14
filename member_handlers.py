#
#  member class for Gig-o-Matic 2 
#
# Aaron Oppenheimer
# 24 August 2013
#

from requestmodel import *

from restify import rest_user_required, CSOR_Jsonify

import member
import gig
import band
import plan
import goemail
import assoc
import login
import datetime
import lang
from colors import colors

import logging


class DefaultPage(BaseHandler):
    """ redirects member to default home view """
    @user_required
    def get(self):
    
        the_new_default=self.request.get("default",None)

        if the_new_default is not None:
            self.user.preferences.default_view = int(the_new_default)
            self.user.put()
    
        view = {
            0: '/agenda.html',
            1: '/calview.html',
            2: '/grid.html'
            }
                
        return self.redirect(view[self.user.preferences.default_view])


class InfoPage(BaseHandler):
    """Page for showing information about a member"""

    @user_required
    def get(self):    
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        the_member_key = member.lookup_member_key(self.request)
        the_member = the_member_key.get()

        ok_to_show = False
        same_band = False
        if the_member_key == the_user.key:
            is_me = True
            ok_to_show = True
        else:
            is_me = False
            
        # find the bands this member is associated with
        the_band_keys=assoc.get_band_keys_of_member_key(the_member_key=the_member_key, confirmed_only=True)
        
        if is_me == False:
            # are we at least in the same band, or superuser?
            if the_user.is_superuser:
                ok_to_show = True
            the_other_band_keys = assoc.get_band_keys_of_member_key(the_member_key=the_user.key, confirmed_only=True)
            for b in the_other_band_keys:
                if b in the_band_keys:
                    ok_to_show = True
                    same_band = True
                    break
            if ok_to_show == False:
                # check to see if we're sharing our profile - if not, bail!
                if (the_member.preferences and the_member.preferences.share_profile == False) and the_user.is_superuser == False:
                    return self.redirect('/')            

        email_change = self.request.get('emailAddressChanged',False)
        if email_change:
            email_change_msg='You have selected a new email address - check your inbox to verify!'
        else:
            email_change_msg = None

        # if I'm not sharing my email, don't share my email
        show_email = False
        if the_member_key == the_user.key or the_user.is_superuser:
            show_email = True
        elif the_member.preferences and the_member.preferences.share_profile and the_member.preferences.share_email:
            show_email = True

        show_phone = False
        if the_member == the_user.key or the_user.is_superuser:
            show_phone = True
        else:
            # are we in the same band? If so, always show email and phone
            if same_band:
                show_phone = True
                show_email = True

        template_args = {
            'the_member' : the_member,
            'the_band_keys' : the_band_keys,
            'member_is_me' : the_user == the_member,
            'email_change_msg' : email_change_msg,
            'show_email' : show_email,
            'show_phone' : show_phone
        }
        self.render_template('member_info.html', template_args)


class EditPage(BaseHandler):

    @user_required
    def get(self):
        self._make_page(the_user=self.user)

    def _make_page(self, the_user, validate_error = None):
        the_member_key = member.lookup_member_key(self.request)
        the_member = the_member_key.get()
        the_cancel_url=self.uri_for("memberinfo",mk=the_member_key.urlsafe())

        template_args = {
            'the_member' : the_member,
            'member_is_me' : the_user == the_member,
            'the_cancel_url' : the_cancel_url,
            'lang' : lang,
            'validate_error' : validate_error
        }
        self.render_template('member_edit.html', template_args)

    def update_preferences(self, the_member):
        if the_member.preferences is None:
            the_member.preferences = member.MemberPreferences()

        member_prefemailnewgig = self.request.get("member_prefemailnewgig", None)
        if (member_prefemailnewgig):
            the_member.preferences.email_new_gig = True
        else:
            the_member.preferences.email_new_gig = False

        member_prefhidecanceledgigs = self.request.get("member_prefhidecanceledgigs", None)
        if (member_prefhidecanceledgigs):
            the_member.preferences.hide_canceled_gigs = True
        else:
            the_member.preferences.hide_canceled_gigs = False

        member_prefshareprofile = self.request.get("member_prefshareprofile", None)
        if (member_prefshareprofile):
            the_member.preferences.share_profile = True
        else:
            the_member.preferences.share_profile = False

        member_prefshareemail = self.request.get("member_prefshareemail", None)
        if (member_prefshareemail):
            the_member.preferences.share_email = True
        else:
            the_member.preferences.share_email = False

        member_prefcalconfirmedonly = self.request.get("member_prefcalconfirmedonly", None)
        if (member_prefcalconfirmedonly):
            the_member.preferences.calendar_show_only_confirmed = True
        else:
            the_member.preferences.calendar_show_only_confirmed = False

        member_prefcalcommittedonly = self.request.get("member_prefcalcommittedonly", None)
        if (member_prefcalcommittedonly):
            the_member.preferences.calendar_show_only_committed = True
        else:
            the_member.preferences.calendar_show_only_committed = False

        member_preflocale = self.request.get("member_preflocale", None)
        if (member_preflocale):
            the_member.preferences.locale = member_preflocale
        else:
            the_member.preferences.locale = "en"

        member_prefagendashowtime = self.request.get("member_prefagendashowtime", None)
        if (member_prefagendashowtime):
            the_member.preferences.agenda_show_time = True
        else:
            the_member.preferences.agenda_show_time = False

    def update_properties(self, the_member):
        # if we're changing email addresses, make sure we're changing to something unique
        member_email = self.request.get("member_email", None)
        if member_email is not None:
            member_email = member_email.lower()

        if member_email is not None and member_email != '' and member_email != the_member.email_address:
            # store the pending address and invite the user to confirm it
            the_member.pending_change_email = member_email
            login.request_new_email(self, member_email)
        else:
            the_member.pending_change_email = ''

        member_name = self.request.get("member_name", None)
        if member_name is not None and member_name != '':
            the_member.name = member_name
        else:
            member_name = None

        member_nickname = self.request.get("member_nickname", None)
        if member_nickname is not None:
            the_member.nickname = member_nickname

        member_phone = self.request.get("member_phone", None)
        if member_phone is not None:
            the_member.phone = member_phone

        member_statement = self.request.get("member_statement", None)
        if member_statement is not None:
            the_member.statement = member_statement

        image_blob = self.request.get("member_images", None)
        image_split = image_blob.split("\n")
        image_urls = []
        for iu in image_split:
            the_iu = iu.strip()
            if the_iu:
                image_urls.append(the_iu)
        the_member.images = image_urls

        member_password1 = self.request.get("member_password1", None)
        if member_password1 is not None and member_password1 != '':
            member_password2 = self.request.get("member_password2", None)
            if member_password2 is not None and member_password2 != '':
                if (member_password1 == member_password2):
                    the_member.set_password(member_password1)
                else:
                    raise MemberError("Passwords do not match")  # redundant to client-side check

        if member_name:
            assoc.change_member_name(the_member.key, member_name)

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""

        validation_error = None
        try:
            the_member_key = member.lookup_member_key(self.request)
            the_member = the_member_key.get()
            self.update_properties(the_member)
            self.update_preferences(the_member)
            the_member.put()
        except member.MemberError as e:
            validation_error = e.value

        if validation_error is not None:
            return self._make_page(self.user, validation_error)
        else:
            return self.redirect(self.uri_for("memberinfo", mk=the_member_key.urlsafe(),
                                              emailAddressChanged=the_member.pending_change_email))


class ManageBandsGetAssocs(BaseHandler):
    """ returns the assocs related to a member """                   
    def post(self):    
        """ return the bands for a member """
        the_member_key = member.lookup_member_key(self.request)
        the_assocs = assoc.get_assocs_of_member_key(the_member_key=the_member_key, confirmed_only=False)

        the_assoc_info=[]
        for an_assoc in the_assocs:
            the_assoc_info.append({
                            'assoc' : an_assoc,
                            'sections' : band.get_section_keys_of_band_key(an_assoc.band)
                            })

        template_args = {
            'the_member' : the_member_key.get(),
            'the_assoc_info' : the_assoc_info,
            'the_colors' : colors
        }
        self.render_template('member_band_assocs.html', template_args)


class ManageBandsGetOtherBands(BaseHandler):
    """ return the popup of other bands """

    def post(self):    
        """ return the bands for a member """
        the_band_keys=assoc.get_band_keys_of_member_key(the_member_key=member.lookup_member_key(self.request), confirmed_only=False)
                    
        every_band = band.get_all_bands()
        all_bands = [a_band for a_band in every_band if a_band.key not in the_band_keys]

        template_args = {
            'all_bands' : all_bands
        }
        self.render_template('member_band_popup.html', template_args)
    
            
class ManageBandsNewAssoc(BaseHandler):
    """ makes a new assoc for a member """                   

    def post(self):    
        """ makes a new assoc for a member """

        the_member_key = member.lookup_member_key(self.request)
        the_band_key=self.request.get('bk','0')
        if the_band_key=='0':
            raise Exception("Band not specified")
            
        the_member = the_member_key.get()
        the_band = band.band_key_from_urlsafe(the_band_key).get()
        
        if assoc.get_assoc_for_band_key_and_member_key(the_band_key = the_band.key, the_member_key = the_member_key) is None:
            assoc.new_association(the_member, the_band)        
            goemail.send_new_member_email(the_band,the_member)
        
        # since our bands are changing, invalidate the band list in our session
        self.user.invalidate_member_bandlists(self, the_member.key)
 

class ManageBandsDeleteAssoc(BaseHandler):
    """ deletes an assoc for a member """

    def get(self):    
        """ deletes an assoc for a member """

        the_assoc_keyurl=self.request.get('ak','0')

        if the_assoc_keyurl == '0':
            return # todo figure out what to do
        
        the_assoc = assoc.assoc_key_from_urlsafe(the_assoc_keyurl).get()
        
        the_member_key=the_assoc.member
        the_band_key=the_assoc.band

        assoc.delete_association_from_key(the_assoc.key)
        plan.delete_plans_for_member_key_for_band_key(the_member_key, the_band_key)
        gig.reset_gigs_for_contact_key(the_member_key, the_band_key)

        # since our bands are changing, invalidate the band list in our session
        self.user.invalidate_member_bandlists(self, the_member_key)
        
        return self.redirect('/member_info.html?mk={0}'.format(the_member_key.urlsafe()))


class SetSection(BaseHandler):
    """ change the default section for a member's band association """
    
    def post(self):
        """ post handler - wants an ak and sk """

        the_user = self.user

        the_section_keyurl=self.request.get('sk','0')
        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')

        if the_section_keyurl=='0' or the_member_keyurl=='0' or the_band_keyurl=='0':
            raise Exception("Section, member and band must all be specified.")

        the_section_key = band.section_key_from_urlsafe(the_section_keyurl)
        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_band_key = band.band_key_from_urlsafe(the_band_keyurl)

        oktochange=False
        if (the_user.key == the_member_key or the_user.is_superuser):
            oktochange=True
        else:
            the_assoc = assoc.get_assoc_for_band_key_and_member_key(the_user.key, the_band_key)
            if the_assoc is not None and the_assoc.is_band_admin:
                oktochange=True

        if (oktochange):
            assoc.set_default_section(the_member_key, the_band_key, the_section_key)

class SetColor(BaseHandler):
    """ change the color for this assoc """

    def post(self):

        the_user = self.user

        the_assoc_keyurl=self.request.get('ak','0')
        the_color=int(self.request.get('c','0'))

        the_assoc_key = assoc.assoc_key_from_urlsafe(the_assoc_keyurl)
        the_assoc = the_assoc_key.get()

        if the_assoc.member == the_user.key:
            the_assoc.color = the_color
            the_assoc.put()


class SetGetEmail(BaseHandler):
    """ change the email reception for this assoc """

    def post(self):

        the_user = self.user

        the_assoc_keyurl=self.request.get('ak','0')
        the_get_email= True if (self.request.get('em','0') == 'true') else False

        the_assoc_key = assoc.assoc_key_from_urlsafe(the_assoc_keyurl)
        the_assoc = the_assoc_key.get()

        if the_assoc.member == the_user.key or the_user.is_superuser:
            the_assoc.email_me= the_get_email
            the_assoc.put()


class SetHideFromSchedule(BaseHandler):
    """ change the schedule-hiding for this assoc """

    def post(self):
        the_assoc_keyurl=self.request.get('ak','0')
        the_do=self.request.get('do',None)

        if the_assoc_keyurl=='0' or the_do is None:
            raise Exception("Association not specified")

        the_hide_me= True if (the_do == 'true') else False

        the_assoc_key = assoc.assoc_key_from_urlsafe(the_assoc_keyurl)
        the_assoc = the_assoc_key.get()

        the_user = self.user
        if the_assoc.member == the_user.key or the_user.is_superuser:
            the_assoc.hide_from_schedule = the_hide_me
            the_assoc.put()


class SetMulti(BaseHandler):
    """ change the default section for a member's band association """
    
    def post(self):
        """ post handler - wants an ak and sk """

        the_member_keyurl=self.request.get('mk','0')
        the_band_keyurl=self.request.get('bk','0')
        the_do=self.request.get('do','')

        if the_band_keyurl=='0' or the_member_keyurl=='0':
            raise Exception("Band or member not specified")
            
        if  the_do=='':
            return

        the_band_key = band.band_key_from_urlsafe(the_band_keyurl)
        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        
        assoc.set_multi(the_member_key, the_band_key, (the_do=='true'))


class AdminPage(BaseHandler):
    """ Page for member administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):
    
        # get all the admin members
        all_band_keys = band.get_all_bands(keys_only=True)
        all_admin_keys = []
        for bk in all_band_keys:
            admin_member_keys = assoc.get_admin_members_from_band_key(bk, keys_only=True)
            for amk in admin_member_keys:
                if not amk in all_admin_keys:
                    all_admin_keys.append(amk)
                    
        all_admin_members = member.get_members_from_keys(all_admin_keys)
        all_admin_emails = [a.email_address for a in all_admin_members]
        
        template_args = {
            'all_admin_emails' : all_admin_emails
        }
        self.render_template('member_admin.html', template_args)


class AdminPageAllMembers(BaseHandler):
    """ Page for member administration """

    @user_required
    @superuser_required
    def post(self):
        the_page_str=self.request.get('p','0')
        the_page=int(the_page_str)
        the_search_str=self.request.get('s', None)
        self._make_page(the_user=self.user, the_page=the_page, the_search=the_search_str)
            
    def _make_page(self,the_user, the_page=0, the_search=None):

        if the_search is None:
            the_members = member.get_all_members(verified_only=True, pagelen=50, page=the_page)
        else:
            the_members = member.search_for_members(verified_only=False, pagelen=50, page=the_page, search=the_search)
        
        member_band_info={}
        for a_member in the_members:
            assocs=assoc.get_assocs_of_member_key(a_member.key, confirmed_only=False)
            member_band_info[a_member.key] = assocs
        
        template_args = {
            'the_members' : the_members,
            'the_band_info' : member_band_info
        }
        self.render_template('member_admin_memberlist.html', template_args)


class AdminPageInviteMembers(BaseHandler):
    """ Page for member administration """
    
    @user_required
    @superuser_required
    def post(self):
        self._make_page(the_user=self.user)

    def _make_page(self,the_user):
    
        the_invite_assocs = assoc.get_all_invites()
        
        template_args = {
            'the_assocs' : the_invite_assocs
        }
        self.render_template('member_admin_invitelist.html', template_args)


class AdminPageSignupMembers(BaseHandler):
    """ Page for member administration """

    @user_required
    @superuser_required
    def post(self):
        self._make_page(the_user=self.user)
            
    def _make_page(self,the_user):
        the_tokens = login.get_all_signup_tokens()
        
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=2)
        limit = now - delta
        for a_token in the_tokens:
            the_member = Member.get_by_id(int(a_token.user))
            if the_member:
                a_token.email = the_member.email_address
            else:
                a_token.email = None

            if a_token.created < limit:
                a_token.is_old=True
        
        template_args = {
            'the_tokens' : the_tokens
        }
        self.render_template('member_admin_signuplist.html', template_args)


class DeleteMember(BaseHandler):
    """ completely delete member """
    
    @user_required
    def get(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')

        if the_member_keyurl=='0':
            return # todo figure out what to do

        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)

        # The only way to get here is to manually paste your key into the url;
        # someone doing that is a troublemaker.
        if not self.user.is_superuser:
            raise MemberError("Cannot delete user because {0} is not a superuser".format(self.user.name))

        if (self.user.key != the_member_key):
            forget_member_from_key(the_member_key)
        else:
            print 'cannot delete yourself, people'

        return self.redirect('/member_admin')


class AdminMember(BaseHandler):
    """ grant or revoke admin rights """
    
    @user_required
    @superuser_required
    def get(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        the_do=self.request.get('do','')

        if the_member_keyurl=='0':
            return # todo figure out what to do

        if the_do=='':
            return # todo figure out what to do

        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_member=the_member_key.get()

        if (the_do=='0'):
            the_member.is_superuser=False
        elif (the_do=='1'):
            the_member.is_superuser=True
        else:
            return # todo figure out what to do

        the_member.put()

        return self.redirect('/member_admin')        


class BetaMember(BaseHandler):
    """ grant or revoke betatester rights """
    
    @user_required
    def get(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        the_do=self.request.get('do','')

        if the_member_keyurl=='0':
            return # todo figure out what to do

        if the_do=='':
            return # todo figure out what to do

        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_member=the_member_key.get()
        
        # todo - make sure the user is a superuser
        if (the_do=='0'):
            the_member.is_betatester=False
        elif (the_do=='1'):
            the_member.is_betatester=True
        else:
            return # todo figure out what to do

        the_member.put()

        return self.redirect('/member_admin')        


class GetBandList(BaseHandler):
    """ return a list of bands """
    
    @user_required
    def post(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        if the_member_keyurl=='0':
            return # todo figure out what to do
        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_bands = self.user.get_band_list(self, the_member_key)

        template_args = {
            'the_bands' : the_bands
        }
        self.render_template('navbar_bandlist.html', template_args)            


class GetAddGigBandList(BaseHandler):
    """ return a list of bands """
    
    @user_required
    def post(self):
        """ post handler - wants a mk """
        
        the_member_keyurl=self.request.get('mk','0')
        if the_member_keyurl=='0':
            return # todo figure out what to do
        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_manage_bands = self.user.get_add_gig_band_list(self, the_member_key)
            
        template_args = {
            'the_bands' : the_manage_bands
        }
        self.render_template('navbar_addgigbandlist.html', template_args)


class RewriteAll(BaseHandler):
    """ get all member objects from the database, and write them back. this will force """
    """ an update to the structure, useful when adding properties. But ugly. """
    
    @user_required
    def get(self):
    
        #  update_all_uniques()
        member.rewrite_all_members()

        self.redirect(self.uri_for('memberadmin'))
        
        
class DeleteInvite(BaseHandler):
    """ remove association with band """
    
    @user_required
    def get(self):
        """ post handler - wants an ak """

        the_assoc_keyurl=self.request.get('ak','0')

        if the_assoc_keyurl=='0':
            return # todo figure out what to do

        the_assoc_key = assoc.assoc_key_from_urlsafe(the_assoc_keyurl)
        the_assoc = the_assoc_key.get()
        
        # make sure we're a band admin or a superuser
        if not (self.user.is_superuser or assoc.get_admin_status_for_member_for_band_key(self.user, the_assoc.band)):
            return self.redirect('/')

        the_band_key = the_assoc.band

        the_member_key = the_assoc.member
        assoc.delete_association_from_key(the_assoc_key) 

        invites = assoc.get_inviting_assoc_keys_from_member_key(the_member_key)
        if invites is None or (len(invites)==1 and invites[0]==the_assoc_key):
            logging.error('removed last invite from member; deleteing')
            forget_member_from_key(the_member_key)            
                    
        return self.redirect('/band_info.html?bk={0}'.format(the_band_key.urlsafe()))


class VerifyMember(BaseHandler):
    """ manually verify a member """
    
    @user_required
    @superuser_required
    def get(self):
        """ handler - wants a mk """

        if not self.user.is_superuser:
            raise MemberError("Cannot verify user because {0} is not a superuser".format(self.user.name))

        the_member_keyurl=self.request.get('mk','0')
        if the_member_keyurl=='0':
            raise MemberError("Cannot verify user because no member key passed in, user={0}".format(self.user.name))
        the_member_key = member.member_key_from_urlsafe(the_member_keyurl)
        the_member = the_member_key.get()

        if the_member is None:
            raise MemberError("Cannot verify user because no member found, user={0}".format(self.user.name))

        the_member.verified = True
        the_member.put()

        return self.redirect('/member_info.html?mk={0}'.format(the_member_keyurl))


##########
#
# REST endpoint stuff
#
##########

def _RestMemberInfo(the_member, include_id=True):
    obj = { k:getattr(the_member,k) for k in ['display_name'] }
    return obj

class RestEndpoint(BaseHandler):

    @rest_user_required
    @CSOR_Jsonify
    def get(self, *args, **kwargs):
        try:
            member_id = kwargs["member_id"]
            the_member = member.member_key_from_urlsafe(member_id).get()
        except:
            self.abort(404)

        # are we authorized to see the member? TODO

        return _RestMemberInfo(the_member, include_id=False)
