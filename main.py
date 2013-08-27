import webapp2
import index
import agenda
import calview
import member
import gig

application = webapp2.WSGIApplication([
    ('/', agenda.MainPage),
    ('/testdata', index.MainPage),
    ('/agenda.html', agenda.MainPage),
    ('/calview.html', calview.MainPage),
    ('/member_info.html', member.InfoPage),
    ('/gig_info.html', gig.InfoPage),
    ('/gig_edit.html', gig.EditPage),
    ('/gig_delete', gig.DeleteHandler),
    ('/calevents', calview.CalEvents),
    ('/agendaevents', agenda.AgendaEvents),
], debug=True)