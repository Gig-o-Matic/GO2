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
        gig.put_gig(gigA)
        gigB = self._create_test_gig(the_band, "B")
        gigB.date = datetime.datetime(2020,8,16)
        gig.put_gig(gigB)

        # set gig A to come before gig B
        gig.set_calltime(gigA, "2:00am")
        gig.put_gig(gigA)
        gig.set_calltime(gigB, "3:00am")
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="A")

        # now make the calltime later for gigA and show that gigB is first
        gig.set_calltime(gigA, "4:00am")
        gig.put_gig(gigA)
        self.assertGigOrder(the_band, total=2, first="B")

        # now make the calltime later for gigB again
        gig.set_calltime(gigB, "5:00am")
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="A")

        # check am/pm issues
        gig.set_calltime(gigA, "12:00pm")
        gig.set_settime(gigA, None)
        gig.put_gig(gigA)
        gig.set_calltime(gigB, "1:00pm")
        gig.set_settime(gigB, None)
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="A")

        # check "none" call times
        gig.set_calltime(gigA, None)
        gig.set_settime(gigA, "1:00 pm")
        gig.put_gig(gigA)
        gig.set_calltime(gigB, "12:00pm")
        gig.set_settime(gigB, None)
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="B")

        # check out other formats of time or not-time
        gig.set_calltime(gigA, "early")
        gig.set_settime(gigA, None)
        gig.put_gig(gigA)
        gig.set_calltime(gigB, "1:00")
        gig.set_settime(gigB, None)
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="A")

        gig.set_calltime(gigA, "2:30pm")
        gig.set_settime(gigA, None)
        gig.put_gig(gigA)
        gig.set_calltime(gigB, "early")
        gig.set_settime(gigB, None)
        gig.put_gig(gigB)
        self.assertGigOrder(the_band, total=2, first="B")






