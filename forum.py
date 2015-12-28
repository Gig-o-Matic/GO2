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

from gig import Gig
import member
from band import Band
import datetime
import logging
import goemail
import assoc

from webapp2_extras.i18n import gettext as _


"""

Forums have a band as a parent
Topics have a forum as a parent and may have a gig as parent, or top-level topic as parent
Posts have another post as parent, or top-level post

"""


#
# classes for forums
#
class Forum(ndb.Model):
    """ Models a gig-o-matic forum """
    name = ndb.StringProperty(default=None) # if it's a band forum, we ignore the name
    public = ndb.BooleanProperty(default=False) # if it's public, anyone can use it

class ForumTopic(ndb.Model):
    """ Models a gig-o-matic forum topic """
    member = ndb.KeyProperty() # creator of topic
    text_id = ndb.TextProperty() # title of topic
    created_date = ndb.DateTimeProperty(auto_now_add=True) # creation date
    last_update = ndb.DateTimeProperty(auto_now=True) # last update
    parent_gig = ndb.KeyProperty( default=None ) # gig, if this is in reference to a gig
    open = ndb.BooleanProperty( default=True )
    approved = ndb.BooleanProperty( default=True )
    pinned = ndb.BooleanProperty( default=False)

class ForumPost(ndb.Model):
    """ Models a gig-o-matic forum post - parent is a topic """
    member = ndb.KeyProperty()
    text_id = ndb.TextProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    pinned = ndb.BooleanProperty(default=False)

#
# helper functions
#

def new_forum(the_band_key, the_name=None, is_public=False):
    """ create a new forum for a band """
    
    the_forum = Forum(parent=the_band_key, name=the_name, public=is_public)
    the_forum.put()

    return the_forum

def get_public_forums(keys_only=False):
    """ get all the forums marked as public """
    
    forum_query = Forum.query(Forum.public==True).order(Forum.name)
    forums = forum_query.fetch(keys_only=keys_only)
    return forums
    

def get_forum_from_band_key(the_band_key, keys_only=False):
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

def delete_forum_key(the_forum_key):
    """ take a forum key and delete the forum, and its posts and text """
    
    topic_keys = get_forumtopics_for_forum_key(the_forum_key, keys_only=True)
    for tk in topic_keys:
        delete_forumtopic(tk)
    
    the_forum_key.delete()
    

def new_forumtopic(the_forum_key, the_member_key, the_title, the_parent_gig_key=None):
    """ create a brand new topic """

    the_document_id = new_forumpost_text(the_title)
    if the_document_id:
        the_topic = ForumTopic(parent=the_forum_key, member=the_member_key, text_id=the_document_id, parent_gig=the_parent_gig_key)
        the_topic.put()
        return the_topic
    else:
        logging.error("failed to create new forum topic")
        return None

def get_forumtopics_for_forum_key(the_forum_key, keys_only=False):
    """ return all of the topics for a forum key """
    
    pinned_topic_query = ForumTopic.query(ForumTopic.pinned==True, ancestor=the_forum_key).order(-ForumTopic.last_update)
    pinned_topics = pinned_topic_query.fetch(keys_only=keys_only)
    unpinned_topic_query = ForumTopic.query(ForumTopic.pinned==False, ancestor=the_forum_key).order(-ForumTopic.last_update)
    unpinned_topics = unpinned_topic_query.fetch(keys_only=keys_only)
    return pinned_topics + unpinned_topics

def get_forumtopic_for_gig_key(the_gig_key):
    """ see if there's a forum for a gig """

    forum_query = ForumTopic.query(ForumTopic.parent_gig == the_gig_key)
    forums = forum_query.fetch()
    if len(forums) == 0:
        return None
    elif len(forums) == 1:
        return forums[0]
    else:
        logging.error("found multiple forum topics for gig {0}".format(the_gig_key))
        return None

def delete_forumtopic_key(the_topic_key):
    """ take a topic key and delete it, and all its posts """
    
    delete_forumposts_for_topic_key(the_topic_key)
    the_topic_key.delete()
    

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

def get_forumposts_from_topic_key(the_topic_key, keys_only=False):
    """ return all posts for a topic key """
    pinned_post_query = ForumPost.query(ForumPost.pinned==True, ancestor=the_topic_key).order(ForumPost.created_date)
    pinned_posts = pinned_post_query.fetch(keys_only=keys_only)
    unpinned_post_query = ForumPost.query(ForumPost.pinned==False, ancestor=the_topic_key).order(ForumPost.created_date)
    unpinned_posts = unpinned_post_query.fetch(keys_only=keys_only)
    return pinned_posts + unpinned_posts

def delete_forumposts_for_topic_key(the_topic_key):
    forumposts = get_forumposts_from_topic_key(the_topic_key)
    for post in forumposts:
        delete_comment(post.text_id)
    ndb.delete_multi([post.key for post in forumposts])


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

        topic_key_str = self.request.get("tk", None)

        the_topic = None
        if topic_key_str is not None:
            the_topic = ndb.Key(urlsafe=topic_key_str).get()
        else:
            logging.error('no topic in AddGigForumPostHandler')
            return # todo - what to do

        if the_topic is None:
            logging.error('no topic in AddGigForumPostHandler')
            return # todo figure out what to do

        comment_str = self.request.get("c", None)
        if comment_str is None or comment_str == '':
            return

        if type(the_topic) is Gig:
            # The topic is a gig, but what we want is a topic. So make a new topic, give it the gig's title,
            # and link it back to the gig.
            the_band_key = the_topic.key.parent()
            the_gig = the_topic
            the_topic = get_forumtopic_for_gig_key(the_topic.key)
            if the_topic is None:
                the_topic = new_forumtopic(get_forum_from_band_key(the_band_key, keys_only=True), self.user.key, the_gig.title, the_parent_gig_key=the_gig.key)

        new_forumpost(the_topic.key, self.user.key, comment_str)
        
        the_topic.put() # force an update
        
        self.response.write('')


class GetGigForumPostHandler(BaseHandler):
    """ returns the posts for a gig if there is one """

    @user_required
    def post(self):

        topic_key_str = self.request.get("tk", None)

        the_topic = None
        if topic_key_str is None:
            logging.error("no topic_key_str in GetGigForumPostHandler")
            return # todo figure this out

        the_topic = ndb.Key(urlsafe=topic_key_str).get()
        
        if type(the_topic) is Gig:
            topic_is_gig = True
            the_gig_topic = get_forumtopic_for_gig_key(the_topic.key)
            if the_gig_topic is None:
                # if there is no topic for a gig, just use the gig - if anyone posts, we'll
                # convert it to a real topic object
                forum_posts = []
                topic_is_open = True # if we're being asked for posts for a gig and there's no topic yet, it's open
            else:
                forum_posts = get_forumposts_from_topic_key(the_gig_topic.key)
                topic_is_open = the_gig_topic.open
        else:
            forum_posts = get_forumposts_from_topic_key(the_topic.key)
            topic_is_open = the_topic.open

        post_text = [get_forumpost_text(p.text_id) for p in forum_posts]

        template_args = {
            'the_topic' : the_topic,
            'the_topic_is_open' : topic_is_open,
            'the_forum_posts' : forum_posts,
            'the_forum_text' : post_text,
            'the_date_formatter' : member.format_date_for_member
        }

        self.render_template('forum_posts.html', template_args)
        
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
        
class ForumHandler(BaseHandler):
    """ shows the forum page for a band """
    
    @user_required
    def get(self):
    
        band_key_str = self.request.get("bk", None)
        if band_key_str is not None:
            the_band_key = ndb.Key(urlsafe=band_key_str)
            the_forum_key = get_forum_from_band_key(the_band_key, True)
        else:
            # not band key - did we get a forum key instead?
            forum_key_str = self.request.get("fk", None)
            if forum_key_str is None:
                logging.error('no band key in ForumHandler')
                return self.redirect('/')
            else:
                the_forum_key = ndb.Key(urlsafe=forum_key_str)
                the_band_key = the_forum_key.parent()

        if the_forum_key is None:
            logging.error('no forum_key in ForumHandler')
            return self.redirect('/')
            
        if the_band_key:
            the_band = the_band_key.get()
        else:
            the_band = None
            
        logging.info('\n\n{0}\n\n'.format(the_band))   
            
        the_topics = get_forumtopics_for_forum_key(the_forum_key, False)
        
        the_topic_titles = [get_forumpost_text(f.text_id) for f in the_topics]
                    
        template_args = {
            'the_forum' : the_forum_key.get(),
            'the_band' : the_band,
            'the_topic_titles' : the_topic_titles,
            'the_topics' : the_topics,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('forum.html', template_args)

class ForumTopicHandler(BaseHandler):
    """ shows a topic page for a band """
    
    @user_required
    def get(self):
    
        topic_key_str = self.request.get("tk", None)
        if topic_key_str is None:
            logging.error('no topic key in ForumTopicHandler')
            return self.redirect('/')
        
        the_topic_key = ndb.Key(urlsafe=topic_key_str)
        the_topic = the_topic_key.get()
        the_forum_key = the_topic_key.parent()
        the_forum = the_forum_key.get()
        the_band_key = the_forum_key.parent()
        
        if the_band_key:
            the_band = the_band_key.get()
            # is the current user a band admin?
            user_is_forum_admin = assoc.get_admin_status_for_member_for_band_key(self.user, the_band_key) or self.user.is_superuser
        else:
            the_band = None
            user_is_forum_admin = self.user.is_superuser
            
        the_gig = the_topic.parent_gig
        
        template_args = {
            'the_forum' : the_forum,
            'the_topic_name' : get_forumpost_text(the_topic.text_id),
            'the_topic' : the_topic,
            'the_gig' : the_gig,
            'user_is_forum_admin' : user_is_forum_admin
        }

        self.render_template('forum_topic.html', template_args)
        
class NewTopicHandler(BaseHandler):
    """ adds a new topic """
    
    @user_required
    def post(self):
    
        forum_key_str = self.request.get("fk", None)
        if forum_key_str is None:
            logging.error('no forum_key_str in NewTopicHandler')
            return self.redirect('/')
            
        forum_key = ndb.Key(urlsafe=forum_key_str)
            
        topic_str = self.request.get("t", None)
        if topic_str is None or topic_str=='':
            logging.error('no topic_str in NewTopicHandler')
            return # todo figure out what to do
            
        the_topic = new_forumtopic(forum_key, self.user.key, topic_str)
        
        return None

class ForumAllTopicsHandler(BaseHandler):
    """ returns all the topics in a forum """
    
    @user_required
    def post(self):
    
        forum_key_str = self.request.get("fk", None)
        if forum_key_str is None:
            logging.error('no forum key in ForumAllTopicsHandler')
            return self.redirect('/')
        
        the_forum_key = ndb.Key(urlsafe=forum_key_str)

        if the_forum_key is None:
            return #
            
        the_topics = get_forumtopics_for_forum_key(the_forum_key, False)
        
        the_topic_titles = []
        goemail.set_locale_for_user(self)
        for a_topic in the_topics:
            the_txt = get_forumpost_text(a_topic.text_id)
            if a_topic.parent_gig is None:
                the_topic_titles.append(the_txt)
            else:
                the_topic_titles.append('{0}: {1}'.format(_("Gig"),the_txt))
            
        # is the current user a forum admin?
        user_is_forum_admin = False
        forum_parent_key = the_forum_key.parent()
        if forum_parent_key:
            forum_parent = forum_parent_key.get()
            if type(forum_parent) is Band:
                user_is_forum_admin = assoc.get_admin_status_for_member_for_band_key(self.user, forum_parent.key)
        else:
            # if there's no parent, this is a public forum and only superuser can edit
            if self.user.is_superuser:
                user_is_forum_admin = True
                
        template_args = {
            'the_forum_key_str' : forum_key_str,
            'user_is_forum_admin' : user_is_forum_admin,
            'the_topic_titles' : the_topic_titles,
            'the_topics' : the_topics,
            'the_date_formatter' : member.format_date_for_member
        }
        self.render_template('forum_topics.html', template_args)
        
class TopicToggleOpenHandler(BaseHandler):
    """ toggles the 'open' state of a topic """
    
    @user_required
    def get(self):
    
        topic_key_str = self.request.get("tk", None)
        if topic_key_str is None:
            logging.error('no topic key in ForumTopicHandler')
            return self.redirect('/')
        
        the_topic_key = ndb.Key(urlsafe=topic_key_str)
        the_topic = the_topic_key.get()
        
        the_band_key = the_topic_key.parent().parent()
    
        # is the current user a band admin?
        user_is_band_admin = assoc.get_admin_status_for_member_for_band_key(self.user, the_band_key)
            
        if not (user_is_band_admin or member.member_is_superuser(self.user)):
            logging.error("non-admin trying to toggle topic state in TopicToggleOpenHandler")
            return self.redirect('/')
            
        the_topic.open = not the_topic.open
        the_topic.put()
        
        return self.redirect('/forum_topic?tk={0}'.format(topic_key_str))  
        
class TogglePinHandler(BaseHandler):
    """ toggles the pin state of a forum topic or post """
    
    @user_required
    def get(self):
        item_key_str = self.request.get("p", None)
        if item_key_str is None:
            logging.error('no object passed to TogglePinHandler')
            return self.redirect('/')
            
        parent_key_str = self.request.get("t", None)
        if parent_key_str is None:
            parent_key_str.error('no topic passed to TogglePinHandler')
            return self.redirect('/')

        logging.info("\n\nparent_key_str is \n\n".format(parent_key_str))

        the_item = ndb.Key(urlsafe=item_key_str).get()
        the_parent = ndb.Key(urlsafe=parent_key_str).get()
        
        if not member.member_is_superuser(self.user):
            logging.error("non-admin trying to toggle pin state in TogglePinHandler")
            return self.redirect('/')

        if the_item is None:
            logging.error("no item found in TogglePinHandler")
            return self.redirect('/')
            
        if the_parent is None:
            logging.error("no parent found in TogglePinHandler")
            return self.redirect('/')

        the_item.pinned = not the_item.pinned
        the_item.put()
        
        if type(the_parent) is ForumTopic:
            return self.redirect('/forum_topic?tk={0}'.format(parent_key_str))
        else:
            return self.redirect('/forum?fk={0}'.format(parent_key_str))
        
class ForumAdminHandler(BaseHandler):
    """ handler for forum admin page """
    
    @superuser_required
    @user_required
    def get(self):
    
        the_forums = get_public_forums()

        template_args = {
            'the_forums' : the_forums
        }
        self.render_template('forum_admin.html', template_args)

class AddForumHandler(BaseHandler):
    """ handler for adding a new public forum """
    
    @superuser_required
    @user_required
    def post(self):
        new_forum_name = self.request.get("forum_name", None)

        if new_forum_name:
            the_new_forum = new_forum(None, the_name=new_forum_name, is_public=True)

        return self.redirect('/forum_admin')
    
class DeleteForumHandler(BaseHandler):
    """ handler for deleting a public forum """
    
    @superuser_required
    @user_required
    def get(self):
    
        the_forum_key_str = self.request.get("fk",None)
        if the_forum_key_str is None:
            logging.error("no forum found in DeleteForumHandler")
            return self.redirect('/')
            
        the_forum_key = ndb.Key(urlsafe=the_forum_key_str)
    
        delete_forum_key(the_forum_key)
        return self.redirect('/forum_admin')
