"""

 crypto class for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 March 2016

"""

from google.appengine.ext import ndb

#
# class for cryptokey
#
class CryptoKey(ndb.Model):
    """ Stores application secrets """

    # for legacy reasons, this is the container for the crypto key
    value = ndb.TextProperty()

    slack_client_id = ndb.TextProperty()
    slack_client_secret = ndb.TextProperty()

def set_cryptokey(value):
    """ sets the crypto key """
    the_cryptokey = get_cryptokey_object()
    if the_cryptokey:
        the_cryptokey.value=value
        the_cryptokey.put()
    else:
        the_cryptokey = CryptoKey(value=value)
        the_cryptokey.put()

def get_cryptokey_object():
    """ Return the cryptokey if there is one """
    cryptokey_query = CryptoKey.query()
    cryptokey = cryptokey_query.fetch(1)
    
    if len(cryptokey) == 0:
        return None
    else:
        return cryptokey[0]
        
def get_cryptokey():
    m = get_cryptokey_object()
    if m:
        return m.value
    else:
        return None
