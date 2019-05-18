#
# tests for band object
#

import unittest
import webapp2
import main
import member
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

    def _make_test_member(self):
        (success, result) = member.create_new_member('foo@bar.com','foo','barbaz')
        self.assertTrue(success)
        return result

    def test_new_member(self):
        the_member = self._make_test_member()
        self.assertIsNotNone(the_member)
        self.assertTrue(isinstance(the_member, member.Member))

        # demonstrate we can get
        check_member = member.get_member(the_member.key)
        self.assertEqual(check_member.name, "foo")

        # demonstrate we can put
        check_member.name = "aaron"
        member.put_member(check_member)

        check2 = member.get_member(check_member.key)
        self.assertEqual(check2.name, "aaron")

if __name__ == '__main__':
    unittest.main()