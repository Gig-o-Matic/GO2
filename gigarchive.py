"""

 archive class for Gig-o-Matic 2 

 Aaron Oppenheimer
 6 October 2013

"""

from webapp2 import RequestHandler
from google.appengine.ext import ndb
import band
import plan
import gig
import assoc
import datetime
import logging
from safetaskqueue import safe_taskqueue_add_bulk, check_taskqueue_trust
from google.appengine.api import search 
from google.appengine.api.taskqueue import taskqueue


def do_autoarchive():
    date = datetime.datetime.now()
    end_date = date - datetime.timedelta(days=3)
    the_gig_keys = gig.get_old_gig_keys(end_date = end_date, max_fetch=10)
    logging.info('found {0} gigs to archive'.format(len(the_gig_keys)))
    paramlist = []
    for a_gig_key in the_gig_keys:
        paramlist.append({'gig_key_urlsafe': a_gig_key.urlsafe()})

    safe_taskqueue_add_bulk(queue_name='archivequeue', url='/do_autoarchive', paramlist=paramlist)

class DoAutoArchiveHandler(RequestHandler):
    def post(self):
        check_taskqueue_trust(self.request)
        the_gig_key_urlsafe = self.request.get('gig_key_urlsafe')
        the_gig_key = gig.gig_key_from_urlsafe(the_gig_key_urlsafe)
        gig.make_archive_for_gig_key(the_gig_key)


def make_archive_for_gig_key(the_gig_key):
    """ makes an archive for a gig - files away all the plans, then delete them """

    the_gig = the_gig_key.get()
    
    the_archive_text = ""
    if the_gig.status == 2: # this gig was cancelled
        the_archive_text="The gig was cancelled."
    else:    
        the_band = the_gig_key.parent().get()
        the_assocs = assoc.get_confirmed_assocs_of_band_key(the_band.key)
        the_sections = list(the_band.sections)
        the_sections.append(None)

        the_plans=[]
        for the_section in the_sections:
            section_plans=[]
            for an_assoc in the_assocs:
                the_plan=plan.get_plan_for_member_key_for_gig_key(an_assoc.member, the_gig_key)
                # add the plan to the list, but only if the member's section for this gig is this section
                if the_plan:
                    test_section = the_plan.section
                    if test_section is None:
                        test_section=an_assoc.default_section
                
                    if test_section == the_section:
                        section_plans.append( [an_assoc.member, the_plan] )

                        # when we file this away, update the member's gig-commitment stats
                        if the_plan.value in [1, 5, 6]:
                            an_assoc.commitment_number = an_assoc.commitment_number + 1

                        # whether or not there's a plan, up the number of gigs we should have committed to
                        an_assoc.commitment_total = an_assoc.commitment_total + 1


            the_plans.append( (the_section, section_plans) )
        ndb.put_multi(the_assocs)


        for a_section in the_plans:
            if a_section[1]:
                the_section_key = a_section[0]
                if (the_section_key):
                    the_section_name=the_section_key.get().name
                else:
                    if len(the_plans)==1:
                        the_section_name=''
                    else:
                        the_section_name='No Section'
                the_archive_text = u'{0}\n{1}'.format(the_archive_text,the_section_name)
        
                for member_plans in a_section[1]:
                    the_member = member_plans[0].get()
                    the_plan = member_plans[1]
                    the_comment = u'- {0}'.format(the_plan.comment) if the_plan.comment else ""
                    the_nickname = u' ({0})'.format(the_member.nickname) if the_member.nickname else ''
                    the_archive_text = u'{0}\n\t{1}{2} - {3} {4}'.format(the_archive_text,
                                                                   the_member.name,
                                                                   the_nickname,
                                                                   plan.plan_text[the_plan.value],
                                                                   the_comment)

                the_archive_text = u'{0}\n'.format(the_archive_text)

    # create a document
    my_document = search.Document(
        fields=[
           search.TextField(name='plans', value=the_archive_text),
           search.TextField(name='type', value='archive')
           ])

    try:
        index = search.Index(name="gigomatic_index")
        result = index.put(my_document)
    except search.Error:
        logging.exception('Put failed')
    
    archive_id = result[0].id    

    if archive_id:
        the_gig = the_gig_key.get()
        if the_gig.archive_id:
            delete_archive(the_gig.archive_id)
        the_gig.archive_id = archive_id
        the_gig.put()
    else:
        logging.error('made archive but did not get document id')
    
def get_archived_plans(archive_id):
    index = search.Index(name="gigomatic_index")
    doc = index.get(archive_id)
    if doc:
        return doc.fields[0].value
    else:
        return ''
   
def delete_archive(archive_id):
    index = search.Index(name="gigomatic_index")
    index.delete([archive_id])
    