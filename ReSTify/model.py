# Define your database model over here

# class HashStore(ndb.Model):
#     """Sample Model
#     Models an individual HashStore entry with hastag, tile, and date.
#     """

#     author = ndb.UserProperty()
#     title = ndb.StringProperty(indexed=False)
#     hashtag = ndb.StringProperty(indexed=True, default="")
#     viewDate = ndb.DateTimeProperty(auto_now_add=True)


Gig = __import__('gig').Gig
Member = __import__('member').Member
