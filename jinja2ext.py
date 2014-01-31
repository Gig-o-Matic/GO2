import jinja2

def html_content(value):
    # Escape, then convert newlines to br tags, then wrap with Markup object
    # so that the <br> tags don't get escaped.
    def escape(s):
        # unicode() forces the conversion to happen immediately,
        # instead of at substitution time (else <br> would get escaped too)
        return unicode(jinja2.escape(s))
    return jinja2.Markup(escape(value).replace('\n', '<br>'))


# jinja_environment.filters['html_content'] = html_content


