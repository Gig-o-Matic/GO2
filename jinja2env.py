import jinja2
import os


def br_escape(value): 
     return value.replace('\n','<br>\n')

def html_content(value):
    # Escape, then convert newlines to br tags, then wrap with Markup object
    # so that the <br> tags don't get escaped.
    def escape(s):
        # unicode() forces the conversion to happen immediately,
        # instead of at substitution time (else <br> would get escaped too)
        return unicode(jinja2.escape(s))
    return jinja2.Markup(escape(value).replace('\n', '<br>'))

def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')

jinja_environment = jinja2.Environment(autoescape=guess_autoescape,
                  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"),
                  extensions=['jinja2.ext.autoescape'])

jinja_environment.filters['html_content'] = html_content

# jinja_environment = jinja2.Environment(
#     loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"),
#     extensions=['jinja2.ext.autoescape'])

