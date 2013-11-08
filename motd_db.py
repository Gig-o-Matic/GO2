"""

 motd class for Gig-o-Matic 2 

 Aaron Oppenheimer
 24 August 2013

"""

from google.appengine.ext import ndb

#
# class for Motd
#
class Motd(ndb.Model):
    """ Models a message of the day """
    value = ndb.TextProperty()

def set_motd(value):
    """ sets the MOTD """
    the_motd = get_motd_object()
    if the_motd:
        the_motd.value=value
        the_motd.put()
    else:
        the_motd = Motd(value=value)
        the_motd.put()
    
        
def get_motd_object():
    """ Return the motd if there is one """
    motd_query = Motd.query()
    motd = motd_query.fetch(1)
    
    if len(motd) == 0:
        return None
    else:
        return motd[0]
        
def get_motd():
    m = get_motd_object()
    if m:
        return m.value
    else:
        return None
