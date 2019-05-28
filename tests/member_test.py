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


    def _make_test_member(self, name):
        (success, result1) = member.create_new_member('{0}@bar.com'.format(name), name, '12345')
        self.assertTrue(success)
        return result1


    def _make_test_band(self):
        return band.new_band("test band")


    def test_new_member(self):
        the_member = self._make_test_member("test1")
        self.assertIsNotNone(the_member)
        self.assertTrue(isinstance(the_member, member.Member))

        # demonstrate we can get
        check_member = member.get_member(the_member.key)
        self.assertEqual(check_member.name, "test1")

        # demonstrate we can put
        check_member.name = "testing1"
        member.put_member(check_member)

        check2 = member.get_member(check_member.key)
        self.assertEqual(check2.name, "testing1")

    def test_urlsafe(self):
        the_member = self._make_test_member("guy")
        test_member = member.member_from_urlsafe(the_member.key.urlsafe())
        self.assertEqual(the_member.key, test_member.key)

    def test_allmembers(self):
        self._make_test_member("guy1")
        self._make_test_member("guy2")
        the_members = member.get_all_members(order=True, keys_only=True, verified_only=False)
        self.assertEqual(len(the_members), 2)
        self.assertTrue(isinstance(the_members[0], ndb.Key))

        the_members = member.get_all_members(order=True, keys_only=False, verified_only=False)
        self.assertEqual(len(the_members), 2)
        self.assertTrue(isinstance(the_members[0], member.Member))

        the_members = member.get_all_members(order=True, keys_only=True, verified_only=True)
        self.assertEqual(len(the_members), 0)

        the_members = member.get_all_members(order=True, keys_only=False, verified_only=False)
        the_members[1].verified = True
        member.put_member(the_members[1])

        the_members = member.get_all_members(order=True, keys_only=True, verified_only=True)
        self.assertEqual(len(the_members), 1)

    def test_password_validator(self):
        pv = member.SimplePasswordValidator(5)
        pv.ensure_valid("12345")
        try:
            pv.ensure_valid("123")
        except member.MemberError:
            pass

    def test_tokens(self):
        m = self._make_test_member("guy")
        t = member.Member.create_email_token(m.get_id())
        m2 = member.Member.get_by_auth_token(m.get_id(), t, 'email')
        self.assertEqual(m.key, m2[0].key)
        member.Member.delete_email_token(m.get_id(), t)
        m2 = member.Member.get_by_auth_token(m.get_id(), t, 'email')
        self.assertIsNone(m2[0])

    def test_band_list(self):
        m = self._make_test_member("joe")
        l = member.Member.get_band_list(None, m.key)
        self.assertEqual(len(l), 0)

if __name__ == '__main__':
    unittest.main()