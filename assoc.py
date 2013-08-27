#
# association class for Gig-o-Matic 2 - links members to bands
#
# Aaron Oppenheimer
# 24 August 2013
#

from google.appengine.ext import ndb
from member import *
from debug import *

def assoc_key(assoc_name='assoc_key'):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('assoc', assoc_name)

#
# class for association
#
class Assoc(ndb.Model):
    """ Models a gig-o-matic association """
    band = ndb.KeyProperty()
    member = ndb.KeyProperty()

def new_association(band, member):
    """ associate a band and a member """
    the_assoc = Assoc(parent=assoc_key(), band=band.key, member=member.key)
    the_assoc.put()

