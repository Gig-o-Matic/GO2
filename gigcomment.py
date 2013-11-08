"""

 comment class for Gig-o-Matic 2 

 Aaron Oppenheimer
 3 November 2013

"""

from google.appengine.api import search 

def add_comment_for_gig(the_comment, the_comment_id=None):
    """ if there's a comment document for a gig, add comment to it; if there isn't one, make one """

    if the_comment_id:
        the_comment_text=get_comment(the_comment_id)
        the_comment_text = '{0}\n-----\n'.format(the_comment_text)
    else:
        the_comment_text=""
        
    the_comment_text = '{0}{1}'.format(the_comment_text,the_comment)
        
    # create a document
    my_document = search.Document(
        doc_id = the_comment_id,
        fields=[
           search.TextField(name='comment', value=the_comment_text),
           search.TextField(name='type', value='comment')
           ])

    try:
        index = search.Index(name="gigomatic_index")
        result = index.put(my_document)
    except search.Error:
        logging.exception('Put failed')
    
    doc_id = result[0].id
    
    return doc_id, the_comment_text
    
def get_comment(comment_id):
    index = search.Index(name="gigomatic_index")
    doc = index.get(comment_id)
    if doc:
        return doc.fields[0].value
    else:
        return ''
   
def delete_comment(comment_id):
    index = search.Index(name="gigomatic_index")
    index.delete([comment_id])
    