#
# tests for gig object
#

import unittest
import webapp2
import main
import gig
import band
from google.appengine.ext import ndb

from google.appengine.ext import testbed


class GigTestCase(unittest.TestCase):

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

    def _make_test_band(self):
        return band.new_band("test band")

    def test_new_gig(self):
        the_band = self._make_test_band()
        the_gig = gig.new_gig(the_band, "test gig", None)
        self.assertIsNotNone(the_gig)
        self.assertIsInstance(the_gig, gig.Gig)

        self.assertEqual(the_gig.status, 0)
        the_gig.set_status(2)
        self.assertEqual(the_gig.status, 2)
        self.assertRaises(ValueError, the_gig.set_status,10)

        the_gig.set_poll()
        self.assertEqual(the_gig.status, 10)
        self.assertRaises(ValueError, the_gig.set_status,0)

        giglist = gig.get_gigs_for_band_keys(the_band.key)
        self.assertEqual(len(giglist),1)
        self.assertEqual(giglist[0].key, the_gig.key)
        



if __name__ == '__main__':
    unittest.main()