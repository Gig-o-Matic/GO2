from webapp2_extras import sessions

import webapp2
import login
import agenda
import grid
import calview
import member
import gig
import plan
import band
import help
import motd
import credits
import maintenance
import stats
import caldav
import activity
import jinja2ext
import os
import cryptoutil
import goemail
import rss
import restify

CONFIG = {
    'webapp2_extras.auth': {
        'user_model': 'member.Member',
        'user_attributes': ['name', 'is_superuser']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'GABBAGABBAHEY'
    },
    'webapp2_extras.jinja2': {
        'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
        'environment_args': {'extensions': ['jinja2.ext.i18n']},
        'filters': {
            'html_content': jinja2ext.html_content,
            'safe_name': jinja2ext.safe_name,
            'good_breaks': jinja2ext.good_breaks,
            'shorten': jinja2ext.shorten,
        }
    },
    'webapp2_extras.i18n': {
        'translations_path': os.path.join(os.path.dirname(__file__), 'locale')
    }
}

if False: # maintenance mode?
    APPLICATION = webapp2.WSGIApplication([(r'/.*', maintenance.MaintenancePage)], config=CONFIG, debug=True)
else:
    APPLICATION = webapp2.WSGIApplication([

        # REST endpoints

        webapp2.Route('/api/authenticate', login.RestLoginEndpoint),
        webapp2.Route('/api/logout', login.RestLogoutEndpoint),
        webapp2.Route('/api/agenda', agenda.RestEndpoint),

        webapp2.Route('/api/plan/<plan_id:.+>/<plan_attribute:.+>', plan.RestEndpoint, methods=['POST']),
        webapp2.Route('/api/plan/<plan_id:.+>/<plan_attribute:.+>/<new_value:.+>', plan.RestEndpoint),
        webapp2.Route('/api/plan/<plan_id:.+>', plan.RestEndpoint),

        webapp2.Route('/api/bands', band.RestEndpointBands),
        webapp2.Route('/api/band/<band_id:.+>', band.RestEndpoint),

        webapp2.Route('/api/gig/plans/<gig_id:.+>', gig.RestEndpointPlans),
        webapp2.Route('/api/gig/<gig_id:.+>', gig.RestEndpoint),

        webapp2.Route('/api/member/<member_id:.+>', member.RestEndpoint),


        # webapp2.Route('/apiX/<endpoint><:/*><values:.*>', restify.Endpoint),

        # Standard endpoints

        webapp2.Route('/', member.DefaultPage, name='home'),
        webapp2.Route('/band/<band_name:.+>', band.InfoPage),
        webapp2.Route('/login', login.LoginPage, name='login'),
        webapp2.Route('/logout', login.LogoutHandler, name='logout'),
        webapp2.Route('/signup', login.SignupPage, name='signup'),
        webapp2.Route('/check_email', login.CheckEmail),
        webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                      handler=login.VerificationHandler, name='verification'),
        webapp2.Route('/<type:e>/<user_id:\d+>-<signup_token:.+>',
                      handler=login.EmailVerificationHandler, name='emailverification'),
        webapp2.Route('/<type:i>/<user_id:\d+>-<signup_token:.+>',
                      handler=login.InviteVerificationHandler, name='inviteverification'),
        webapp2.Route('/link_error', login.LinkErrorHandler, name='linkerror'),
        webapp2.Route('/forgot', login.ForgotPasswordHandler, name='forgot'),
        webapp2.Route('/password', login.SetPasswordHandler),
        webapp2.Route('/invitepassword', login.InviteVerificationHandler),
        webapp2.Route('/admin_login_auto_old_token', login.AutoDeleteSignupTokenHandler),
        webapp2.Route('/help', help.HelpHandler),
        webapp2.Route('/changelog', help.ChangeLogHandler),
        webapp2.Route('/privacy', help.PrivacyHandler),
        webapp2.Route('/help_band_request.html', help.SignUpBandHandler),
        webapp2.Route('/credits', credits.CreditsHandler),
        webapp2.Route('/seen_welcome', motd.SeenWelcomeHandler),
        webapp2.Route('/seen_motd', motd.SeenHandler),
        webapp2.Route('/agenda.html', agenda.MainPage),
        webapp2.Route('/agenda.html', agenda.MainPage, name='agenda'),
        webapp2.Route('/agenda_switch', agenda.SwitchView),
        webapp2.Route('/grid.html', grid.MainPage),
        webapp2.Route('/calview.html', calview.MainPage),
        webapp2.Route('/member_info.html', member.InfoPage, name='memberinfo'),
        webapp2.Route('/member_edit.html', member.EditPage),
        webapp2.Route('/member_get_assocs', member.ManageBandsGetAssocs, name='getassocs'),
        webapp2.Route(
            '/member_get_other_bands',
            member.ManageBandsGetOtherBands,
            name='getotherbands'),
        webapp2.Route('/member_new_assoc', member.ManageBandsNewAssoc, name='newassoc'),
        webapp2.Route(
            '/member_delete_assoc.html',
            member.ManageBandsDeleteAssoc,
            name='deleteassoc'),
        webapp2.Route('/member_admin', member.AdminPage, name="memberadmin"),
        webapp2.Route('/member_admin_get_all_members', member.AdminPageAllMembers),
        webapp2.Route('/member_admin_get_signup_members', member.AdminPageSignupMembers),
        webapp2.Route('/member_admin_get_invite_members', member.AdminPageInviteMembers),
        webapp2.Route('/member_delete_invite', member.DeleteInvite),
        webapp2.Route('/member_makeadmin', member.AdminMember),
        webapp2.Route('/member_makebeta', member.BetaMember),
        webapp2.Route('/member_delete', member.DeleteMember),
        webapp2.Route('/member_set_section', member.SetSection),
        webapp2.Route('/member_set_color', member.SetColor),
        webapp2.Route('/member_set_get_email', member.SetGetEmail),
        webapp2.Route('/member_set_hide_from_schedule', member.SetHideFromSchedule),
        webapp2.Route('/member_set_multi', member.SetMulti),
        webapp2.Route('/member_get_bands', member.GetBandList),
        webapp2.Route('/member_get_add_gig_bands', member.GetAddGigBandList),
        webapp2.Route('/member_rewrite', member.RewriteAll),
        webapp2.Route('/verify_member', member.VerifyMember),
        webapp2.Route('/gig_info.html', gig.InfoPage, name="gig_info"),
        webapp2.Route('/gig_edit.html', gig.EditPage),
        webapp2.Route('/gig_archive', gig.ArchiveHandler),
        webapp2.Route('/admin_gig_autoarchive', gig.AutoArchiveHandler),
        webapp2.Route('/gig_delete', gig.DeleteHandler),
        webapp2.Route('/gig_restore_trashed', gig.RestoreHandler),
        webapp2.Route('/gig_add_comment', gig.CommentHandler),
        webapp2.Route('/gig_get_comment', gig.GetCommentHandler),
        webapp2.Route('/gig_answerlink',gig.AnswerLinkHandler, name="gig_answerlink"),
        webapp2.Route('/print_setlist', gig.PrintSetlist),
        webapp2.Route('/print_planlist', gig.PrintPlanlist),
        webapp2.Route('/member_spreadsheet', band.MemberSpreadsheet),
        webapp2.Route('/archive_spreadsheet', band.ArchiveSpreadsheet),
        webapp2.Route('/sendreminder', gig.SendReminder),
        webapp2.Route('/band_info.html', band.InfoPage),
        webapp2.Route('/band_edit.html', band.EditPage),
        webapp2.Route('/band_delete.html', band.DeleteBand),
        webapp2.Route('/band_get_members', band.BandGetMembers, name='getmembers'),
        webapp2.Route('/band_get_sections', band.BandGetSections, name='getsections'),
        webapp2.Route('/band_setup_sections', band.SetupSections, name='setupSections'),
        webapp2.Route('/band_confirm_member', band.ConfirmMember),
        webapp2.Route('/band_makeadmin', band.AdminMember),
        webapp2.Route('/band_makeoccasional', band.MakeOccasionalMember),
        webapp2.Route('/band_removemember', band.RemoveMember),
        webapp2.Route('/band_admin', band.AdminPage),
        webapp2.Route('/band_get_member_list', band.GetMemberList),
        webapp2.Route('/band_nav.html', band.BandNavPage),
        webapp2.Route('/band_get_upcoming', band.GetUpcoming),
        webapp2.Route('/band_get_public_members', band.GetPublicMembers),
        webapp2.Route('/band_invite.html', band.InvitePage),
        webapp2.Route('/band_send_invites', band.SendInvites),
        webapp2.Route('/band_activity', activity.MainPage),
        webapp2.Route('/band_gig_archive', band.GigArchivePage),
        webapp2.Route('/band_gig_trashcan', band.GigTrashcanPage),
        webapp2.Route('/calevents', calview.CalEvents),
        webapp2.Route('/updateplan', plan.UpdatePlan),
        webapp2.Route('/updateplanfeedback', plan.UpdatePlanFeedback),
        webapp2.Route('/updateplancomment', plan.UpdatePlanComment),
        webapp2.Route('/updateplansection', plan.UpdatePlanSection),
        webapp2.Route('/admin_send_reminders', plan.SendReminders),
        webapp2.Route('/motd_admin', motd.AdminPage),
        webapp2.Route('/crypto_admin', cryptoutil.AdminPage, name='crypto_admin'),
        webapp2.Route('/whatis.html', login.WhatisPageHandler),
        webapp2.Route('/stats', stats.StatsPage),
        webapp2.Route('/admin_generate_stats', stats.AutoGenerateStats),
        webapp2.Route('/cal/b/<bk:.+>', caldav.BandRequestHandler),
        webapp2.Route('/cal/m/<mk:.+>', caldav.MemberRequestHandler),
        webapp2.Route('/cal/p/<bk:.+>', caldav.PublicBandGigRequestHandler),
        webapp2.Route('/calhelp', caldav.HelpHandler),
        webapp2.Route('/announce_new_gig_handler',goemail.AnnounceNewGigHandler),
        webapp2.Route('/send_new_gig_handler',goemail.SendNewGigHandler),
        webapp2.Route('/rss/<bk:.+>',rss.GetRssHandler),
        webapp2.Route('/make_rss_feed_handler',rss.MakeRssFeedHandler)
    ], config=CONFIG, debug=True)
