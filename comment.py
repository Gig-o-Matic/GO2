#
# comment class for Gig-o-Matic 2 - member comments on gigs. Replaces the old "gigcomment" class
#
# Aaron Oppenheimer
# 25 April 2014
#

from google.appengine.ext import ndb

import gig
import member
import datetime

#
# class for comment
#
class Comment(ndb.Model):
    """ Models a gig-o-matic plan """
    member = ndb.KeyProperty()
    comment = ndb.TextProperty()
    created_date = ndb.DateTimeProperty( auto_now_add=True )

def new_comment(the_gig_key, the_member_key, the_text):
    """ create a new comment """
    the_comment = Comment(parent=the_gig_key, member=the_member_key, comment=the_text)
    the_comment.put()
    return the_comment

def get_comments_from_gig_key(the_gig_key, keys_only=False):
    """ return comments for a gig key """
    comment_query = Comment.query(ancestor=the_gig_key).order(Comment.created_date)
    comments = comment_query.fetch(keys_only=keys_only)
    return comments
    
def delete_comments_for_gig_key(the_gig_key):
    comment_keys = get_comments_from_gig_key(the_gig_key, keys_only=True)
    ndb.delete_multi(comment_keys)
