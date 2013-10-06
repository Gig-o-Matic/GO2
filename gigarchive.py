"""

 archive class for Gig-o-Matic 2 

 Aaron Oppenheimer
 6 October 2013

"""

import band
import plan
import gig

from google.appengine.api import search 

def make_archive_for_gig_key(the_gig_key):
    """ makes an archive for a gig - files away all the plans, then delete them """

    the_members_by_section = band.get_member_keys_of_band_key_by_section_key(the_gig_key.parent())
    the_gig = the_gig_key.get()
    the_band = the_gig_key.parent().get()
    
    the_plans=[]
    for the_section in the_members_by_section:
        section_plans=[]
        for a_member_key in the_section[1]:
            the_plan=plan.get_plan_for_member_for_gig(a_member_key.get(), the_gig)
            # add the plan to the list, but only if the member's section for this gig is this section
            if the_plan and the_plan.section == the_section[0]:
                section_plans.append( [a_member_key, the_plan] )
        the_plans.append( (the_section[0], section_plans) )
    
    the_archive_text = ""
    for a_section in the_plans:
        the_section_key = a_section[0]
        if (the_section_key):
            the_section_name=the_section_key.get().name
        else:
            the_section_name='None'
        the_archive_text = '{0}\n{1}'.format(the_archive_text,the_section_name)
        
        for member_plans in a_section[1]:
            the_member = member_plans[0].get()
            the_plan = member_plans[1]
            the_comment = '- {0}'.format(the_plan.comment) if the_plan.comment else ""
            the_archive_text = '{0}\n\t{1} - {2} {3}'.format(the_archive_text,
                                                           the_member.name,
                                                           plan.plan_text[the_plan.value],
                                                           the_comment)

    # create a document
    my_document = search.Document(
        fields=[
           search.TextField(name='plans', value=the_archive_text),
           ])

    try:
        index = search.Index(name="gigomatic_index")
        result = index.put(my_document)
    except search.Error:
        logging.exception('Put failed')
    
    doc_id = result[0].id
    
    print 'got document ID {0}'.format(doc_id)
    
    return doc_id
    
def delete_archive(archive_id):
    index = search.Index(name="gigomatic_index")
    index.delete([archive_id])
    