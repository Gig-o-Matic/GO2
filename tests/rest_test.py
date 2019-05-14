import unittest
import webapp2
import main
import agenda
import band
import member
import assoc
import gig
import datetime

from google.appengine.ext import testbed

class RestTestCase(unittest.TestCase):
    TEST_RECIPIENT = 'alice@example.com'
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

    def _create_test_band_with_member(self, member_is_admin = True):
        the_band = band.new_band(self.TEST_BAND)
        (member_created, the_member) = member.create_new_member(self.TEST_RECIPIENT, 'Alice', 'password')
        self.assertTrue(member_created)

        membership = assoc.Assoc();
        membership.band = the_band.key
        membership.member = the_member.key
        membership.is_confirmed = True
        if member_is_admin:
            membership.is_band_admin = True
        membership.put()

        return (the_band, the_member)

    def test_rest_api_agenda(self):
        # Create band with member and instantiate a gig
        the_band, the_member = self._create_test_band_with_member()

        # verify that we have no gig for this band
        (upcoming_plans, weighin_plans, number_of_bands) = agenda._get_agenda_contents_for_member(the_member)
        self.assertEmpty(upcoming_plans)
        self.assertEmpty(weighin_plans)

        # add a gig
        the_gig = gig.new_gig(the_band, "Parade", the_member.key, date=datetime.datetime.now() + datetime.timedelta(days=2))

        # verify that we now have one gig for this band
        (upcoming_plans, weighin_plans, number_of_bands) = agenda._get_agenda_contents_for_member(the_member)
        self.assertEmpty(upcoming_plans)
        self.assertEqual(len(weighin_plans),1)
        self.assertEqual(len(weighin_plans[0].keys()),6)


if __name__ == '__main__':
    unittest.main()