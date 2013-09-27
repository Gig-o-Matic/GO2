from webapp2_extras import sessions

import webapp2
import login
import index
import agenda
import calview
import member
import gig
import plan
import band

config = {
  'webapp2_extras.auth': {
    'user_model': 'member.Member',
    'user_attributes': ['name', 'role']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'GABBAGABBAHEY'
  }
}

application = webapp2.WSGIApplication([
    webapp2.Route('/', agenda.MainPage),
    webapp2.Route('/testdata', index.MainPage),
    webapp2.Route('/testmail', index.TestMail),
    webapp2.Route('/login', login.LoginPage, name='login'),
    webapp2.Route('/logout', login.LogoutHandler, name='logout'),
    webapp2.Route('/signup', login.SignupPage, name='signup'),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                  handler=login.VerificationHandler, name='verification'),
    webapp2.Route('/forgot', login.ForgotPasswordHandler, name='forgot'),                  
    webapp2.Route('/password', login.SetPasswordHandler),
    webapp2.Route('/agenda.html', agenda.MainPage, name='home'),
    webapp2.Route('/agenda.html', agenda.MainPage, name='agenda'),
    webapp2.Route('/calview.html', calview.MainPage),
    webapp2.Route('/member_info.html', member.InfoPage, name='memberinfo'),
    webapp2.Route('/member_edit.html', member.EditPage),
    webapp2.Route('/member_get_assocs.html', member.ManageBandsGetAssocs, name='getassocs'),
    webapp2.Route('/member_new_assoc', member.ManageBandsNewAssoc, name='newassoc'),
    webapp2.Route('/member_delete_assoc.html', member.ManageBandsDeleteAssoc, name='deleteassoc'),
    webapp2.Route('/member_add_section.html', member.AddSectionForMemberForBand, name='addsection'),
    webapp2.Route('/member_leave_section.html', member.LeaveSectionForMemberForBand, name='leavesection'),
    webapp2.Route('/member_new_default_section', member.NewDefaultSection),
    webapp2.Route('/member_admin.html', member.AdminPage),
    webapp2.Route('/member_makeadmin', member.AdminMember),
    webapp2.Route('/member_delete', member.DeleteMember),
    webapp2.Route('/gig_info.html', gig.InfoPage),
    webapp2.Route('/gig_edit.html', gig.EditPage),
    webapp2.Route('/gig_delete', gig.DeleteHandler),
    webapp2.Route('/band_info.html',band.InfoPage),
    webapp2.Route('/band_edit.html',band.EditPage),
    webapp2.Route('/band_get_members',band.BandGetMembers, name='getmembers'),
    webapp2.Route('/band_get_sections',band.BandGetSections, name='getsections'),
    webapp2.Route('/band_new_section',band.NewSection),
    webapp2.Route('/band_delete_section',band.DeleteSection),
    webapp2.Route('/band_move_section',band.MoveSection),
    webapp2.Route('/band_confirm_member',band.ConfirmMember),
    webapp2.Route('/band_makeadmin', band.AdminMember),
    webapp2.Route('/band_removemember', band.RemoveMember),
    webapp2.Route('/band_admin.html', band.AdminPage),    
    webapp2.Route('/calevents', calview.CalEvents),
    webapp2.Route('/updateplan', plan.UpdatePlan),
    webapp2.Route('/updateplancomment', plan.UpdatePlanComment),
    webapp2.Route('/updateplansection', plan.UpdatePlanSection)
], config=config, debug=True)