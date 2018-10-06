import jwt
from crypto_db import get_cryptokey

def make_jwt(userid):
	cryptokey = get_cryptokey()
	encoded = jwt.encode({'user': userid}, cryptokey, algorithm='HS256')
	return encoded

def decode_jwt(token):
	cryptokey = get_cryptokey()
	decoded = jwt.decode(token,cryptokey, algorithm='HS256')
	return decoded['user']