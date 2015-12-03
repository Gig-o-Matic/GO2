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

"""

Forums have a band as a parent
Threads have a forum as a parent and may have a gig as parent, or top-level thread as parent
Posts have another post as parent, or top-level post

"""


#
# classes for forums
#
class Forum(ndb.Model):
    """ Models a gig-o-matic forum """
    name = ndb.TextProperty(default = None) # empty field; there's no need for a real name

class ForumThread(ndb.Model):
    """ Models a gig-o-matic forum thread """
    member = ndb.KeyProperty() # creator of thread
    text_id = ndb.TextProperty() # title of thread
    created_date = ndb.DateTimeProperty(auto_now_add=True) # creation date
    parent_gig = ndb.KeyProperty() # gig, if this is in reference to a gig

class ForumPost(ndb.Model):
    """ Models a gig-o-matic forum post - parent is a thread """
    member = ndb.KeyProperty()
    text_id = ndb.TextProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)

#
# helper functions
#

def new_forum(the_band_key):
    """ create a new forum for a band """
    
    the_forum = Forum(parent=the_band_key)
    the_forum.put()

    return the_forum

def get_forum_from_band_key(the_band_key, keys_only):
    """ given a band key, find the associated forum or make a new one """
    
    forum_query = Forum.query(ancestor=the_band_key)
    forums = forum_query.fetch(keys_only=keys_only)
    
    if len(forums) == 0:
        the_forum = new_forum(the_band_key)
        if keys_only:
            return the_forum.key
        else:
            return the_forum
    elif len(forums) == 1:
        return forums[0]
    else:
        logging.error("found multiple forums for band {0}".format(the_band_key))
        return None


def new_forumthread(the_forum_key, the_member_key, the_title, the_parent_gig=None):
    """ create a brand new thread """

    the_document_id = new_forumpost_text(the_title)
    if the_document_id:
        the_thread = ForumThread(parent=the_forum_key, member=the_member_key, text_id=the_document_id, parent_gig=the_parent_gig)
        the_thread.put()
        return the_thread
    else:
        logging.error("failed to create new forum thread")
        return None


def get_forumthread_for_gig_key(the_gig_key):
    """ see if there's a forum for a gig """

    forum_query = ForumThread.query(ForumThread.parent_gig == the_gig_key)
    forums = forum_query.fetch()
    if len(forums) == 0:
        return None
    elif len(forums) == 1:
        return forums[0]
    else:
        logging.error("found multiple forum threads for gig {0}".format(the_gig_key))
        return None

def new_forumpost(the_parent_key, the_member_key, the_text):
    """ create a new post """

    the_document_id = new_forumpost_text(the_text)

    if the_document_id:
        the_post = ForumPost(parent=the_parent_key, member=the_member_key, text_id=the_document_id)
        the_post.put()
        return the_post
    else:
        logging.error("failed to create new forum post")
        return None

def get_forumposts_from_thread_key(the_thread_key, keys_only=False):
    """ return comments for a gig key """
    post_query = ForumPost.query(ancestor=the_thread_key).order(ForumPost.created_date)
    posts = post_query.fetch(keys_only=keys_only)
    return posts

def delete_forumposts_for_thread_key(the_thread_key):
    forumpost_keys = get_forumposts_from_thread_key(the_thread_key, keys_only=True)
    ndb.delete_multi(forumpost_keys)


def new_forumpost_text(the_text):
    """ make a new searchable 'document' for this post """

    # create a document
    my_document = search.Document(
        doc_id=None,
        fields=[search.TextField(name='comment', value=the_text)])

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


#
# Response handlers for dealing with forums
#
class AddGigForumPostHandler(BaseHandler):
    """ takes a new comment and adds it to the gig """

    @user_required
    def post(self):

        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            logging.error('no gig key string in addgigforumposthandler')
            return # todo figure out what to do if there's no ID passed in


        parent_key_str = self.request.get("pk", None)
        if parent_key_str is None:
            return # todo figure out what to do if there's no ID passed in

        the_parent = ndb.Key(urlsafe=parent_key_str).get()

        if type(the_parent) is gig.Gig:
            the_thread = get_forumthread_for_gig_key(ndb.Key(urlsafe=gig_key_str))

            if the_thread is None:
                the_parent = new_forumthread(get_forum_from_band_key(ndb.Key(urlsafe=gig_key_str).parent(), True), self.user.key, the_parent.title, the_parent_gig=the_parent.key)
            else:
                the_parent = the_thread

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str == '':
            return

        new_forumpost(the_parent.key, self.user.key, comment_str)
        self.response.write('')


class GetGigForumPostHandler(BaseHandler):
    """ returns the posts for a gig if there is one """

    @user_required
    def post(self):

        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            return # todo figure out what to do if there's no ID passed in
        the_gig_key = ndb.Key(urlsafe=gig_key_str)

        the_thread = get_forumthread_for_gig_key(the_gig_key)

        if the_thread:
            forum_posts = get_forumposts_from_thread_key(the_thread.key)
            post_text = [get_forumpost_text(p.text_id) for p in forum_posts]
        else:
            forum_posts = []
            post_text = []

        template_args = {
            'the_gig' : the_gig_key.get(),
            'the_forum_posts' : forum_posts,
            'the_forum_text' : post_text,
            'the_date_formatter' : member.format_date_for_member
        }

        self.render_template('forumposts.html', template_args)
        
class OpenPostReplyHandler(BaseHandler):
    """ returns the HTML required for text entry for a post reply """
    
    @user_required
    def post(self):
    
        post_key_str = self.request.get("pk", None)
        if post_key_str is None:
            logging.error('no post key in openpostreplyhandler')
            return # todo figure out what to do if there's no ID passed in

        gig_key_str = self.request.get("gk", None)
        if gig_key_str is None:
            logging.error('no gig key in openpostreplyhandler')
            return # todo figure out what to do if there's no ID passed in
    
        template_args = {
            'post_key_string' : post_key_str,
            'gig_key_string' : gig_key_str
        }
    
        self.render_template('forumpostreply.html', template_args)
    
