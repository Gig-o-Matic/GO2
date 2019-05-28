#
# tests for band object
#

import unittest
import webapp2
import main
import band
import band_handlers
from google.appengine.ext import ndb

from google.appengine.ext import testbed


class BandTestCase(unittest.TestCase):

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

    def test_info_page(self):
        the_band = self._make_test_band()
        handler = band_handlers.InfoPage()
        res = handler.get(band_name="test band")
        raise ValueError("fix this")

if __name__ == '__main__':
    unittest.main()