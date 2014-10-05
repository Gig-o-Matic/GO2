# http://stackoverflow.com/questions/14314344/how-to-copy-all-entities-in-a-kind-in-gae-to-another-kind-without-explicitly-cal

from google.appengine.ext import ndb


def clone_entity(e, to_klass, **extra_args):
    """Clones an entity, adding or overriding constructor attributes.

    The cloned entity will have exactly the same property values as the original
    entity, except where overridden or missing in to_klass. By default it will have 
    no parent entity or key name, unless supplied.

    Args:
      e: The entity to clone
      to_klass: The target class
      extra_args: Keyword arguments to override from the cloned entity and pass
        to the constructor.
    Returns:
      A cloned, possibly modified, instance of to_klass with the same properties as e.
    """
    klass = e.__class__
    props = dict((k, v.__get__(e, klass))
                 for k, v in klass._properties.iteritems()
                 if type(v) is not ndb.ComputedProperty
    )
    props.update(extra_args)
    allowed_props = to_klass._properties
    for key in props.keys():
        if key not in allowed_props:
            del props[key]
    return to_klass(parent=e.key.parent(),**props)