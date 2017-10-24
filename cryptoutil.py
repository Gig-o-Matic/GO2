"""

 crypto utils for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 March 2016

"""

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models
import webapp2

import crypto_db
import member
from Crypto.Cipher import AES
import binascii


# Utilities for encrypting stuff

def encrypt_string(the_string):
 
    key = crypto_db.get_cryptokey()
 
    encobj = AES.new(key, AES.MODE_ECB)
    
    # pad out the string to a multiple of 16
    x = 16-(len(the_string) % 16)
    if x < 16:
        the_string_pad = '{: <{}}'.format(the_string,len(the_string)+x)
    else:
        the_string_pad = the_string
    
    ciphertext = encobj.encrypt(the_string_pad)
 
    # Resulting ciphertext in hex
    return ciphertext.encode('hex') 


def decrypt_string(the_string):
 
    key = crypto_db.get_cryptokey()
    ciphertext = binascii.unhexlify(the_string)
 
    decobj = AES.new(key, AES.MODE_ECB)
    plaintext = decobj.decrypt(ciphertext)
 
    # Resulting plaintext
    return plaintext


# handler function for crypto key admin

class AdminPage(BaseHandler):
    """ Page for cryptokey administration """

    @user_required
    def get(self):
        if member.member_is_superuser(self.user):
            self._make_page(the_user=self.user)
        else:
            return self.redirect('/')            
            
    def _make_page(self,the_user):

        secrets = crypto_db.get_cryptokey_object()

        template_args = {
            'cryptokey' : crypto_db.get_cryptokey(),
            'slack_client_id': secrets.slack_client_id,
            'slack_client_secret': secrets.slack_client_secret
        }

        self.render_template('secrets_admin.html', template_args)


    @user_required
    def post(self):
        the_cryptokey=self.request.get('cryptokey','')
        # pad out the string to 32 characters
        the_cryptokey = '{:_<32}'.format(the_cryptokey)

        crypto_db.set_cryptokey(the_cryptokey)

        secrets = crypto_db.get_cryptokey_object()
        secrets.slack_client_id = self.request.get('slack_client_id')
        secrets.slack_client_secret = self.request.get('slack_client_secret')
        secrets.put()

        # testing
        input_str = 'boom!!!'
        encrypted_str=encrypt_string(input_str)
        if decrypt_string(encrypted_str).strip() != input_str:
            raise RuntimeError("Crypto error!")

        self.redirect(self.uri_for('secrets_admin'))
