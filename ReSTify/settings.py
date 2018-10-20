# Add the URL of the site requesting the ReST server i.e. origin of request to the ReST server*/
ORIGIN_SITE_NAME = "http://example.com"

# Alias name for the models, If you dont want to expose you Model name or for a neat URL
MODEL_NAME_ALIAS = {
  'gig': 'Gig',
  'member': 'Member'
  }

# List of fields in the model to expose. If the model isn't here, everything is exposed.
MODEL_EXPOSE = {
	'member': ['name']
}