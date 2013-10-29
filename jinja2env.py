import jinja2
import os


def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')

jinja_environment = jinja2.Environment(autoescape=guess_autoescape,
                  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"),
                  extensions=['jinja2.ext.autoescape'])


# jinja_environment = jinja2.Environment(
#     loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"),
#     extensions=['jinja2.ext.autoescape'])

