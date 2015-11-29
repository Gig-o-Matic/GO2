#
# forum system for the gig-o-matic
#
# Aaron Oppenheimer
# 28 November 2015
#

from google.appengine.ext import ndb
from requestmodel import *
import webapp2_extras.appengine.auth.models

import webapp2

from google.appengine.api import search 
from google.appengine.ext import ndb

import gig
import member
import datetime
import logging

#
# class for forum post
#
class ForumPost(ndb.Model):
    """ Models a gig-o-matic forum post """
    member = ndb.KeyProperty()
    text_id = ndb.TextProperty()
    created_date = ndb.DateTimeProperty( auto_now_add=True )

def new_forumpost(the_gig_key, the_member_key, the_text):
    """ create a new post """
    
    the_document_id = new_forumpost_text(the_text)
    
    logging.info('document id is {0}'.format(the_document_id))
    
    if the_document_id:
        the_post = ForumPost(parent=the_gig_key, member=the_member_key, text_id=the_document_id)
        the_post.put()
        return the_post

def get_forumposts_from_gig_key(the_gig_key, keys_only=False):
    """ return comments for a gig key """
    post_query = ForumPost.query(ancestor=the_gig_key).order(ForumPost.created_date)
    posts = post_query.fetch(keys_only=keys_only)
    return posts
    
def delete_forumposts_for_gig_key(the_gig_key):
    forumpost_keys = get_forumposts_from_gig_key(the_gig_key, keys_only=True)
    ndb.delete_multi(forumpost_keys)


def new_forumpost_text(the_text):
    """ make a new searchable 'document' for this post """

    # create a document
    my_document = search.Document(
        doc_id = None,
        fields=[
           search.TextField(name='comment', value=the_text),
           ])

    try:
        index = search.Index(name="gigomatic_forum_index")
        result = index.put(my_document)
    except search.Error:
        logging.exception('Put failed')
    
    doc_id = result[0].id
    
    return doc_id
    
def get_forumpost_text(forumpost_id):
    index = search.Index(name="gigomatic_forum_index")
    doc = index.get(forumpost_id)
    if doc:
        return doc.fields[0].value
    else:
        return ''
   
def delete_comment(forumpost_id):
    index = search.Index(name="gigomatic_forum_index")
    index.delete([forumpost_id])



class AddForumPostHandler(BaseHandler):
    """ takes a new comment and adds it to the gig """

    @user_required
    def post(self):
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in

        the_gig_key = ndb.Key(urlsafe=gig_key_str)

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str=='':
            return

        new_forumpost(the_gig_key, self.user.key, comment_str)
        self.response.write('')        

class GetForumPostHandler(BaseHandler):
    """ returns the comment for a gig if there is one """
    
    @user_required
    def post(self):
    
        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig = ndb.Key(urlsafe=gig_key_str).get()

        forum_posts = get_forumposts_from_gig_key(the_gig.key)
        post_text = [get_forumpost_text(p.text_id) for p in forum_posts]
        
        logging.info("\n\nTEXT = {0}\n\n".format(post_text))
        
        template_args = {
            'the_forum_posts' : forum_posts,
            'the_forum_text' : post_text,
            'the_date_formatter' : member.format_date_for_member            
        }
        
        self.render_template('forumposts.html', template_args)
        