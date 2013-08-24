import webapp2
import index

application = webapp2.WSGIApplication([
    ('/', index.MainPage),
], debug=True)