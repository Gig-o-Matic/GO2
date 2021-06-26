"""

 sendgrid api class for Gig-o-Matic 2 

 Aaron Oppenheimer
 21 June 2021

"""

from google.appengine.ext import ndb

#
# class for sendgrid API
#
class SendgridAPI(ndb.Model):
    """ Models a crypto key """
    value = ndb.TextProperty()

def set_sendgrid_api(value):
    """ sets the sendgrid api key """
    the_sendgrid_api = get_sendgrid_api_object()
    if the_sendgrid_api:
        the_sendgrid_api.value=value
        the_sendgrid_api.put()
    else:
        the_sendgrid_api = SendgridAPI(value=value)
        the_sendgrid_api.put()
    
        
def get_sendgrid_api_object():
    """ Return the sendgrid_api if there is one """
    sendgrid_api_query = SendgridAPI.query()
    sendgrid_api = sendgrid_api_query.fetch(1)
    
    if len(sendgrid_api) == 0:
        return None
    else:
        return sendgrid_api[0]
        
def get_sendgrid_api():
    m = get_sendgrid_api_object()
    if m:
        return m.value
    else:
        return None
