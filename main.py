import webapp2
import index
import agenda
import calview
import member_info
import gig_info
import gig_edit
import calevents

application = webapp2.WSGIApplication([
    ('/', agenda.MainPage),
    ('/testdata', index.MainPage),
    ('/agenda.html', agenda.MainPage),
    ('/calview.html', calview.MainPage),
    ('/member_info.html', member_info.MainPage),
    ('/gig_info.html', gig_info.MainPage),
    ('/gig_edit.html', gig_edit.MainPage),
    ('/calevents', calevents.MainPage),
], debug=True)