from webapp2_extras import sessions

import webapp2
import login
import agenda
import grid
import calview
import member
import member_handlers
import gig_handlers
import plan
import band_handlers
import help
import motd
import credits
import maintenance
import stats
import caldav
import gigarchive
import jinja2ext
import os
import cryptoutil
import captchautil
import goemail
import rss

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

if False:  # maintenance mode?
    APPLICATION = webapp2.WSGIApplication([(r'/.*', maintenance.MaintenancePage)], config=CONFIG, debug=True)
else:
    APPLICATION = webapp2.WSGIApplication([

        # REST endpoints

        webapp2.Route('/api/authenticate', login.RestLoginEndpoint),
        webapp2.Route('/api/session', login.RestSessionEndpoint),
        webapp2.Route('/api/logout', login.RestLogoutEndpoint),
        webapp2.Route('/api/agenda', agenda.RestEndpoint),

        webapp2.Route('/api/plan/<plan_id:.+>/<plan_attribute:.+>', plan.RestEndpoint, methods=['POST']),
        webapp2.Route('/api/plan/<plan_id:.+>/<plan_attribute:.+>/<new_value:.+>', plan.RestEndpoint),
        webapp2.Route('/api/plan/<plan_id:.+>', plan.RestEndpoint),

        webapp2.Route('/api/bands', band_handlers.RestEndpointBands),
        webapp2.Route('/api/band/members/<band_id:.+>', band_handlers.RestEndpointMembers),
        webapp2.Route('/api/band/<band_id:.+>', band_handlers.RestEndpoint),

        webapp2.Route('/api/gig/plans/<gig_id:.+>', gig_handlers.RestEndpointPlans),
        webapp2.Route('/api/gig/<gig_id:.+>', gig_handlers.RestEndpoint),

        webapp2.Route('/api/member/<member_id:.+>', member_handlers.RestEndpoint),


        # webapp2.Route('/apiX/<endpoint><:/*><values:.*>', restify.Endpoint),

        # Standard endpoints

        webapp2.Route('/', member_handlers.DefaultPage, name='home'),
        webapp2.Route('/band/<band_name:.+>', band_handlers.InfoPage),
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
        webapp2.Route('/gridnew.html', grid.MainPageNew),
        webapp2.Route('/grid_guts', grid.Guts),
        webapp2.Route('/calview.html', calview.MainPage),
        webapp2.Route('/member_info.html', member_handlers.InfoPage, name='memberinfo'),
        webapp2.Route('/member_edit.html', member_handlers.EditPage),
        webapp2.Route('/member_get_assocs', member_handlers.ManageBandsGetAssocs, name='getassocs'),
        webapp2.Route(
            '/member_get_other_bands',
            member_handlers.ManageBandsGetOtherBands,
            name='getotherbands'),
        webapp2.Route('/member_new_assoc', member_handlers.ManageBandsNewAssoc, name='newassoc'),
        webapp2.Route(
            '/member_delete_assoc.html',
            member_handlers.ManageBandsDeleteAssoc,
            name='deleteassoc'),
        webapp2.Route('/member_admin', member_handlers.AdminPage, name="memberadmin"),
        webapp2.Route('/member_admin_get_all_members', member_handlers.AdminPageAllMembers),
        webapp2.Route('/member_admin_get_signup_members', member_handlers.AdminPageSignupMembers),
        webapp2.Route('/member_admin_get_invite_members', member_handlers.AdminPageInviteMembers),
        webapp2.Route('/member_delete_invite', member_handlers.DeleteInvite),
        webapp2.Route('/member_makeadmin', member_handlers.AdminMember),
        webapp2.Route('/member_makebeta', member_handlers.BetaMember),
        webapp2.Route('/member_delete', member_handlers.DeleteMember),
        webapp2.Route('/member_set_section', member_handlers.SetSection),
        webapp2.Route('/member_set_color', member_handlers.SetColor),
        webapp2.Route('/member_set_get_email', member_handlers.SetGetEmail),
        webapp2.Route('/member_set_hide_from_schedule', member_handlers.SetHideFromSchedule),
        webapp2.Route('/member_set_multi', member_handlers.SetMulti),
        webapp2.Route('/member_get_bands', member_handlers.GetBandList),
        webapp2.Route('/member_get_add_gig_bands', member_handlers.GetAddGigBandList),
        webapp2.Route('/member_rewrite', member_handlers.RewriteAll),
        webapp2.Route('/verify_member', member_handlers.VerifyMember),
        webapp2.Route('/gig_info.html', gig_handlers.InfoPage, name="gig_info"),
        webapp2.Route('/gig_edit.html', gig_handlers.EditPage),
        webapp2.Route('/gig_archive', gig_handlers.ArchiveHandler),
        webapp2.Route('/admin_gig_autoarchive', gig_handlers.AutoArchiveHandler),
        webapp2.Route('/do_autoarchive', gigarchive.DoAutoArchiveHandler),
        webapp2.Route('/gig_delete', gig_handlers.DeleteHandler),
        webapp2.Route('/gig_restore_trashed', gig_handlers.RestoreHandler),
        webapp2.Route('/gig_add_comment', gig_handlers.CommentHandler),
        webapp2.Route('/gig_get_comment', gig_handlers.GetCommentHandler),
        webapp2.Route('/gig_answerlink', gig_handlers.AnswerLinkHandler, name="gig_answerlink"),
        webapp2.Route('/print_setlist', gig_handlers.PrintSetlist),
        webapp2.Route('/print_planlist', gig_handlers.PrintPlanlist),
        webapp2.Route('/member_spreadsheet', band_handlers.MemberSpreadsheet),
        webapp2.Route('/member_emails', band_handlers.MemberEmails),
        webapp2.Route('/archive_spreadsheet', band_handlers.ArchiveSpreadsheet),
        webapp2.Route('/sendreminder', gig_handlers.SendReminder),
        webapp2.Route('/band_info.html', band_handlers.InfoPage),
        webapp2.Route('/band_edit.html', band_handlers.EditPage),
        webapp2.Route('/band_edit_test_new_member_message', band_handlers.TestNewMemberMessage),
        webapp2.Route('/band_delete.html', band_handlers.DeleteBand),
        webapp2.Route('/band_get_members', band_handlers.BandGetMembers, name='getmembers'),
        webapp2.Route('/band_get_sections', band_handlers.BandGetSections, name='getsections'),
        webapp2.Route('/band_setup_sections', band_handlers.SetupSections, name='setupSections'),
        webapp2.Route('/band_confirm_member', band_handlers.ConfirmMember),
        webapp2.Route('/band_makeadmin', band_handlers.AdminMember),
        webapp2.Route('/band_makeoccasional', band_handlers.MakeOccasionalMember),
        webapp2.Route('/band_removemember', band_handlers.RemoveMember),
        webapp2.Route('/band_admin', band_handlers.AdminPage),
        webapp2.Route('/band_get_member_list', band_handlers.GetMemberList),
        webapp2.Route('/band_nav.html', band_handlers.BandNavPage),
        webapp2.Route('/band_get_upcoming', band_handlers.GetUpcoming),
        webapp2.Route('/band_get_public_members', band_handlers.GetPublicMembers),
        webapp2.Route('/band_invite.html', band_handlers.InvitePage),
        webapp2.Route('/band_send_invites', band_handlers.SendInvites),
        webapp2.Route('/band_gig_archive', band_handlers.GigArchivePage),
        webapp2.Route('/band_gig_trashcan', band_handlers.GigTrashcanPage),
        webapp2.Route('/calevents', calview.CalEvents),
        webapp2.Route('/updateplan', plan.UpdatePlan),
        webapp2.Route('/updateplanfeedback', plan.UpdatePlanFeedback),
        webapp2.Route('/updateplancomment', plan.UpdatePlanComment),
        webapp2.Route('/updateplansection', plan.UpdatePlanSection),
        webapp2.Route('/admin_send_reminders', plan.SendReminders),
        webapp2.Route('/motd_admin', motd.AdminPage),
        webapp2.Route('/crypto_admin', cryptoutil.AdminPage, name='crypto_admin'),
        webapp2.Route('/captcha_admin', captchautil.AdminPage, name='captcha_admin'),
        webapp2.Route('/whatis.html', login.WhatisPageHandler),
        webapp2.Route('/stats', stats.StatsPage),
        webapp2.Route('/admin_generate_stats', stats.AutoGenerateStats),
        webapp2.Route('/cal/b/<bk:.+>', caldav.BandRequestHandler),
        webapp2.Route('/cal/m/<mk:.+>', caldav.MemberRequestHandler),
        webapp2.Route('/cal/p/<bk:.+>', caldav.PublicBandGigRequestHandler),
        webapp2.Route('/calhelp', caldav.HelpHandler),
        webapp2.Route('/announce_new_gig_handler', goemail.AnnounceNewGigHandler),
        webapp2.Route('/send_new_gig_handler', goemail.SendNewGigHandler),
        webapp2.Route('/rss/<bk:.+>', rss.GetRssHandler),
        webapp2.Route('/make_rss_feed_handler', rss.MakeRssFeedHandler),
        webapp2.Route('/_ah/bounce', goemail.LogBounceHandler),
        webapp2.Route('/_ah/mail/<address:.+>', goemail.IncomingEmailHandler),
        webapp2.Route('/mail_admin', goemail.AdminPage),
        webapp2.Route('/email_admin_test_email', goemail.SendTestEmail),
        webapp2.Route('/send_test_email_handler', goemail.SendTestEmailHandler),
        webapp2.Route('/member_test_email', goemail.MemberTestEmail),
        webapp2.Route('/member_test_email_handler', goemail.MemberTestEmailHandler),
    ], config=CONFIG, debug=True)
