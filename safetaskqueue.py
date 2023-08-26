from google.appengine.api.taskqueue import taskqueue
import cryptoutil


def safe_taskqueue_add(queue_name, url, params):
    params['the_key'] = cryptoutil.encrypt_string("Trust Me")
    taskqueue.add(queue_name=queue_name, url=url, params=params)

def safe_taskqueue_add_bulk(queue_name, url, paramlist):
    the_key = cryptoutil.encrypt_string("Trust Me")
    for p in paramlist:
        p['the_key'] = the_key
        taskqueue.add(queue_name=queue_name, url=url, params=p)

def check_taskqueue_trust(request):
    the_key = request.get('the_key','')
    plain_key = cryptoutil.decrypt_string(the_key).strip()
    if not plain_key == "Trust Me":
        raise RuntimeError('bad key to send email from {0}'.format(request.remote_addr))
