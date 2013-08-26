from google.appengine.api import users
import webapp2
from gig import *
from member import *
from band import *
from utils import *
from assoc import *

from jinja2env import jinja_environment as je
import debug
import datetime

class MainPage(webapp2.RequestHandler):

    def get(self):
        print 'GIG_EDIT GET HANDLER'
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.make_page(user)

    def make_page(self, user):
        debug_print('IN GIG_EDIT {0}'.format(user.nickname()))
        
        member=get_member_from_nickname(user.nickname())
        debug_print('member is {0}'.format(str(member)))
        
        if member is None:
            return # todo figure out what to do if we get this far and there's no member

        if self.request.get("new",None) is not None:
            gig=None
            gig_id=0
            band=get_current_band(member)
            band_id=band.key.id()
        else:
            band_id=self.request.get("band_id",None)
            gig_id=self.request.get("gig_id", None)
            band,gig=get_band_and_gig(band_id, gig_id)
            if band is None or gig is None:
                self.response.write('did not find a band or gig!')
                return # todo figure out what to do if we didn't find it
            debug_print('found gig object: {0}'.format(gig.title))
                    
        template = je.get_template('gig_edit.html')
        self.response.write( template.render(
            title='Gig Edit',
            member=member,
            logout_link=users.create_logout_url('/'),            
            gig=gig,
            gig_id=gig_id,
            band_id=band_id
        ) )        

    def post(self):
        """post handler - if we are edited by the template, handle it here and redirect back to info page"""
        print 'GIG_EDIT POST HANDLER'

        print str(self.request.arguments())

        band_id=int(self.request.get("band_id",None))
        gig_id=int(self.request.get("gig_id", None))
        
        print 'GIG ID IS {0}'.format(gig_id)
        
        if gig_id==0:
            band=get_band_from_id(band_id)
            gig=new_gig(band,'tmp')
            gig_id=gig.key.id()
        else:
            band,gig=get_band_and_gig(band_id, gig_id)

        if band is None or gig is None:
            self.response.write('did not find a band of gig!')
            return # todo figure out what to do if we didn't find it
       
        gig_title=self.request.get("gig_title",None)
        if gig_title is not None and gig_title != '':
            print 'got title {0}'.format(gig_title)
            gig.title=gig_title
        
        gig_details=self.request.get("gig_details",None)
        if gig_details is not None and gig_details != '':
            print 'got details {0}'.format(gig_details)
            gig.details=gig_details

        gig_date=self.request.get("gig_date",None)
        if gig_date is not None and gig_date != '':
            print 'got date {0}'.format(gig_date)
            gig.date=datetime.datetime.strptime(gig_date,'%m/%d/%Y').date()
            # todo validate form entry so date isn't bogus

        gig.put()            

        return self.redirect('/gig_info.html?band_id={0}&gig_id={1}'.format(band_id, gig_id))
        