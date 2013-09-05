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
    webapp2.Route('/login', login.LoginPage, name='login'),
    webapp2.Route('/logout', login.LogoutHandler, name='logout'),
    webapp2.Route('/signup', login.SignupPage, name='signup'),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                  handler=login.VerificationHandler, name='verification'),
    webapp2.Route('/agenda.html', agenda.MainPage, name='home'),
    webapp2.Route('/calview.html', calview.MainPage),
    webapp2.Route('/member_info.html', member.InfoPage),
    webapp2.Route('/member_edit.html', member.EditPage),
    webapp2.Route('/gig_info.html', gig.InfoPage),
    webapp2.Route('/gig_edit.html', gig.EditPage),
    webapp2.Route('/gig_delete', gig.DeleteHandler),
    webapp2.Route('/band_info.html',band.InfoPage),
    webapp2.Route('/band_edit.html',band.EditPage),
    webapp2.Route('/calevents', calview.CalEvents),
    webapp2.Route('/updateplan', plan.UpdatePlan),
    webapp2.Route('/updateplancomment', plan.UpdatePlanComment)
], config=config, debug=True)