import unittest
import webapp2
import main
import band
import member
import assoc
import gig
import datetime

from google.appengine.ext import testbed

class TrashcanTestCase(unittest.TestCase):
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
        if member_is_admin:
            membership.is_band_admin = True
        membership.put()

        return (the_band, the_member)

    def test_gig_trashcan(self):
        # Create band with member and instantiate a gig
        the_band, the_member = self._create_test_band_with_member()
        the_gig = gig.new_gig(the_band, "Parade", the_member.key)

        # verify that we have one gig for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEqual(len(all_gigs),1)

        # put the gig in the trash can
        the_gig.trashed_date = datetime.datetime.now()
        self.assertTrue(the_gig.is_in_trash)
        the_gig.put()

        # verify that we now have no gigs for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEmpty(all_gigs)

        # verify that we have one trashed gig
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = None)
        self.assertEqual(len(trash_gigs),1)

        # take band out of trash
        the_gig.trashed_date = None
        self.assertFalse(the_gig.is_in_trash)
        the_gig.put()

        # verify that we have one gig for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEqual(len(all_gigs),1)

        # verify that we have no trashed gigs
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = None)
        self.assertEmpty(trash_gigs)


    def test_delete_trash(self):
        # Create band with member and instantiate a gig
        the_band, the_member = self._create_test_band_with_member()
        the_gig = gig.new_gig(the_band, "Parade", the_member.key)

        # verify that we have one gig for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEqual(len(all_gigs),1)

        # sweep for trashed gigs and make sure we didn't lose this one
        gig._do_autoarchive()

        # verify that we have one gig for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEqual(len(all_gigs),1)

        # put the gig in the trash can 20 days ago
        the_gig.trashed_date = datetime.datetime.now() - datetime.timedelta(days=20)
        self.assertTrue(the_gig.is_in_trash)
        the_gig.put()

        # sweep for trashed gigs and make sure we didn't lose this one
        gig._do_autoarchive()

        # verify that we now have no gigs for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEmpty(all_gigs)

        # verify that we have one trashed gig
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 0)
        self.assertEqual(len(trash_gigs),1)

        # verify that we have no month-old trashed gigs
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 30)
        self.assertEmpty(trash_gigs)

        # put the gig in the trash can 31 days ago
        the_gig.trashed_date = datetime.datetime.now() - datetime.timedelta(days=31)
        the_gig.put()

        # sweep for trashed gigs and make sure we didn't lose this one
        gig._do_autoarchive()

        # verify that we now have no gigs for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEmpty(all_gigs)

        # verify that we have no trashed gig
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 0)
        self.assertEmpty(trash_gigs)

    def test_selective_delete(self):
        # Create band with member and instantiate a couple of gigs
        the_band, the_member = self._create_test_band_with_member()
        the_gig1 = gig.new_gig(the_band, "Parade1", the_member.key)
        the_gig2 = gig.new_gig(the_band, "Parade2", the_member.key)

        # verify that we have two gigs for this band
        all_gigs = gig.get_gigs_for_band_keys([the_band.key])
        self.assertEqual(len(all_gigs),2)

        # verify that we have no trashed gig
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 0)
        self.assertEmpty(trash_gigs)

        the_gig1.trashed_date = datetime.datetime.now() - datetime.timedelta(days=20)
        self.assertTrue(the_gig1.is_in_trash)
        the_gig1.put()

        the_gig2.trashed_date = datetime.datetime.now() - datetime.timedelta(days=31)
        self.assertTrue(the_gig2.is_in_trash)
        the_gig2.put()

        # show two gigs in the trash
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 0)
        self.assertEqual(len(trash_gigs),2)

        # sweep the trash
        gig._do_autoarchive()

        # now should be one in the trash
        trash_gigs = gig.get_old_trashed_gigs(minimum_age = 0)
        self.assertEqual(len(trash_gigs),1)



if __name__ == '__main__':
    unittest.main()