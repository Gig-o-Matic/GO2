import jinja2

def html_content(value):
    # Escape, then convert newlines to br tags, then wrap with Markup object
    # so that the <br> tags don't get escaped.
    def escape(s):
        # unicode() forces the conversion to happen immediately,
        # instead of at substitution time (else <br> would get escaped too)
        return unicode(jinja2.escape(s))
    return jinja2.Markup(escape(value).replace('\n', '<br>'))

def safe_name(value):
    # Replace single quote with something
    ret=""
    for c in value:
        if c == "'":
            ret = ret + "\\'"
        else: 
            ret = ret + c
    return ret

def good_breaks(value):
    # convert newlines to br tags, then wrap with Markup object
    # so that the <br> tags don't get escaped.
    return jinja2.Markup(value.replace('\n', '<br>'))

def shorten(value):
    if len(value) > 8:
        return value[:8]+'...'
    else:
        return value