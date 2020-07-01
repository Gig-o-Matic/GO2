"""

 crypto utils for Gig-o-Matic 2 

 Aaron Oppenheimer
 4 March 2016

"""

from requestmodel import *

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
 
    try:
        key = crypto_db.get_cryptokey()
        ciphertext = binascii.unhexlify(the_string)
    
        decobj = AES.new(key, AES.MODE_ECB)
        plaintext = decobj.decrypt(ciphertext)
    except TypeError:
        return None
 
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
    
        template_args = {
            'current' : crypto_db.get_cryptokey()
        }
        self.render_template('crypto_admin.html', template_args)


    @user_required
    def post(self):
        the_cryptokey=self.request.get('cryptokey_content','')
        # pad out the string to 32 characters
        the_cryptokey = '{:_<32}'.format(the_cryptokey)

        crypto_db.set_cryptokey(the_cryptokey)
        
        # testing
        str1=encrypt_string('boom!!!')
        str2=decrypt_string(str1)
        
        self.redirect(self.uri_for('crypto_admin'))

