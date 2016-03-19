#
# searchable text for the gig-o-matic
#
# Aaron Oppenheimer
# 19 March 2015
#

from google.appengine.api import search


def new_search_text(the_text,the_item_key_str,the_type_str,the_typevalue_str):
    """ make a new searchable 'document' for this post """

    # create a document
    my_document = search.Document(
        doc_id=None,
        fields=[
                    search.TextField(name='text', value=the_text),
                    search.TextField(name='item', value=the_item_key_str),
                    search.TextField(name='type', value=the_type_str),
                    search.TextField(name='value', value=the_typevalue_str)
                ])

    try:
        index = search.Index(name="gigomatic_searchtext_index")
        result = index.put(my_document)
    except search.Error:
        logging.exception('Put failed')

    doc_id = result[0].id

    return doc_id

def get_search_text(searchtext_id):
    index = search.Index(name="gigomatic_searchtext_index")
    doc = index.get(searchtext_id)
    if doc:
        return doc.fields[0].value
    else:
        return ''

def delete_search_text(searchtext_id):
    index = search.Index(name="gigomatic_searchtext_index")
    index.delete([searchtext_id])
    
def search_search_text(text, the_type, the_value): # forum_key_urlsafe):
    index = search.Index(name="gigomatic_searchtext_index")

    found=[]

    if the_value:
        query = search.Query('"{0}" type: {1} value: {2}'.format(text, the_type, the_value))
    else:
        query = search.Query('{0}'.format(text))

    try:
        results = index.search(query) 

                    
    except search.Error:
        logging.exception('Search failed')
        return []

    return results


