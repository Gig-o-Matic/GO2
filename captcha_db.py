"""

 captcha keys for Gig-o-Matic 2 

 Aaron Oppenheimer
 6 June 2020

"""

from google.appengine.ext import ndb

#
# class for reCaptcha keys
#
class CaptchaKeys(ndb.Model):
    """ Models a crypto key """
    site_key = ndb.TextProperty()
    secret_key = ndb.TextProperty()
    threshold = ndb.FloatProperty(default=0.5)

def set_captchakeys(site_key, secret_key, threshold):
    """ sets the captcha key """
    the_captchakeys = get_captchakeys_object()
    if the_captchakeys:
        the_captchakeys.site_key=site_key
        the_captchakeys.secret_key=secret_key
        the_captchakeys.threshold=threshold
        the_captchakeys.put()
    else:
        the_captchakeys = CaptchaKeys(site_key=site_key, secret_key=secret_key, threshold=threshold)
        the_captchakeys.put()
    
        
def get_captchakeys_object():
    """ Return the captchakey if there is one """
    captchakey_query = CaptchaKeys.query()
    captchakey = captchakey_query.fetch(1)
    
    if len(captchakey) == 0:
        return None
    else:
        return captchakey[0]
        
def get_captchakeys():
    m = get_captchakeys_object()
    if m:
        return m
    else:
        return None
