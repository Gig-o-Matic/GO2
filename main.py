import webapp2
import index
import agenda
import member_info
import gig_info
import gig_edit

application = webapp2.WSGIApplication([
    ('/', index.MainPage),
    ('/agenda.html', agenda.MainPage),
    ('/member_info.html', member_info.MainPage),
    ('/gig_info.html', gig_info.MainPage),
    ('/gig_edit.html', gig_edit.MainPage),
], debug=True)