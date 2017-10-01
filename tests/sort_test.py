import unittest
import webapp2
import main
import band
import gig
import datetime


from google.appengine.ext import testbed

class GigSortTestCase(unittest.TestCase):
    TEST_BAND = 'Wild Rumpus'

    # Needed to get webapp2 to use a WSGIApplication application instance,
    # which is easier to configure in setUp().
    webapp2._local = None

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # Need to set up a global application and Request instance for
        # the i18n module to work. There's probably a more elegant way
        # of doing this.
        self.request_stub = webapp2.Request.blank("/")
        self.request_stub.user = None
        self.request_stub.app = main.APPLICATION
        webapp2.WSGIApplication.app = main.APPLICATION
        webapp2.get_app().set_globals(main.APPLICATION, self.request_stub)

    def tearDown(self):
        self.testbed.deactivate()

    def assertNotEmpty(self, obj):
        self.assertTrue(obj is not None and len(obj) > 0)

    def assertEmpty(self, obj):
        self.assertTrue(obj is not None and len(obj) == 0)

    def _create_test_band(self):
        the_band = band.new_band(self.TEST_BAND)
        self.assertIsNotNone(the_band, "did not create band")
        return (the_band)

    def _create_test_gig(self, band, name):
        the_gig = gig.new_gig(band, name, None)
        self.assertIsNotNone(the_gig, "did not create gig " + name)
        return (the_gig)

    def assertGigOrder(self, band, total, first):
        all_gigs = gig.get_sorted_gigs_from_band_keys([band.key])
        self.assertEqual(len(all_gigs),total,"did not get {0} gigs".format(total))
        self.assertTrue(all_gigs[0].title==first, "'{0}' did not come first".format(first))

    def test_gig_sort(self):
    	the_band = self._create_test_band()
        gigA = self._create_test_gig(the_band, "A")
        gigA.date = datetime.datetime(2020,8,16)
        gigA.put()
        gigB = self._create_test_gig(the_band, "B")
        gigB.date = datetime.datetime(2020,8,16)
        gigB.put()

        # set gig A to come before gig B
        gigA.set_calltime("2:00am")
        gigA.put()
        gigB.set_calltime("3:00am")
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="A")

        # now make the calltime later for gigA and show that gigB is first
        gigA.set_calltime("4:00am")
        gigA.put()
        self.assertGigOrder(the_band, total=2, first="B")

        # now make the calltime later for gigB again
        gigB.set_calltime("5:00am")
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="A")

        # check am/pm issues
        gigA.set_calltime("12:00pm")
        gigA.set_settime(None)
        gigA.put()
        gigB.set_calltime("1:00pm")
        gigB.set_settime(None)
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="A")

        # check "none" call times
        gigA.set_calltime(None)
        gigA.set_settime("1:00 pm")
        gigA.put()
        gigB.set_calltime("12:00pm")
        gigB.set_settime(None)
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="B")

        # check out other formats of time or not-time
        gigA.set_calltime("early")
        gigA.set_settime(None)
        gigA.put()
        gigB.set_calltime("1:00")
        gigB.set_settime(None)
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="A")

        gigA.set_calltime("2:30pm")
        gigA.set_settime(None)
        gigA.put()
        gigB.set_calltime("early")
        gigB.set_settime(None)
        gigB.put()
        self.assertGigOrder(the_band, total=2, first="B")






