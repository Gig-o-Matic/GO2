import webapp2
import index
import agenda
import calview
import member
import gig
import plan

application = webapp2.WSGIApplication([
    ('/', agenda.MainPage),
    ('/testdata', index.MainPage),
    ('/agenda.html', agenda.MainPage),
    ('/calview.html', calview.MainPage),
    ('/member_info.html', member.InfoPage),
    ('/member_edit.html', member.EditPage),
    ('/gig_info.html', gig.InfoPage),
    ('/gig_edit.html', gig.EditPage),
    ('/gig_delete', gig.DeleteHandler),
    ('/calevents', calview.CalEvents),
    ('/updateplan', plan.UpdatePlan),
    ('/updateplancomment', plan.UpdatePlanComment)
], debug=True)