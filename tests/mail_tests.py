import unittest
import webapp2
import goemail
import main
import band
import member
import assoc
import gig
import crypto_db

from google.appengine.ext import testbed

class MailTestCase(unittest.TestCase):
    TEST_RECIPIENT = 'alice@example.com'
    TEST_BAND = 'Wild Rumpus'
    TEST_URL = 'http://example.com'

    # Needed to get webapp2 to use a WSGIApplication application instance,
    # which is easier to configure in setUp().
    webapp2._local = None

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_mail_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

        crypto_db.set_cryptokey('dead0000dead0000')

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

    def _get_single_message(self):
        messages = self.mail_stub.get_sent_messages(to=self.TEST_RECIPIENT)
        self.assertEqual(len(messages), 1)
        return messages[0]

    def assertWellFormedAndContainsText(self, recipient, text):
        message = self._get_single_message()
        self.assertEqual(message.sender, goemail._admin_email_address)
        self.assertEqual(message.to, recipient)
        self.assertNotEmpty(message.subject)
        self.assertRegexpMatches(message.body.payload, text)

    def test_registration_email(self):
        goemail.send_registration_email(self.TEST_RECIPIENT, self.TEST_URL)
        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, self.TEST_URL)

    def test_band_accepted_email(self):
        the_band = band.new_band(self.TEST_BAND)
        goemail.send_band_accepted_email(self.TEST_RECIPIENT, the_band)

        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, self.TEST_BAND)

    def test_forgot_email(self):
        goemail.send_forgot_email(self.TEST_RECIPIENT, self.TEST_URL)
        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, self.TEST_URL)

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

    def test_newgig_email(self):
        # Create band with member and instantiate a gig
        the_band, the_member = self._create_test_band_with_member()
        the_gig = gig.new_gig(the_band, "Parade", the_member.key)

        goemail.send_newgig_email(the_member, the_gig, the_band, self.TEST_URL, True, True)
        message = self._get_single_message()
        self.assertEqual(message.to, self.TEST_RECIPIENT)
        self.assertNotEmpty(message.subject)
        self.assertRegexpMatches(message.body.payload, self.TEST_URL)
        self.assertRegexpMatches(message.body.payload, "Parade")

    def test_new_member_email(self):
        the_band, the_member = self._create_test_band_with_member()
        goemail.send_new_member_email(the_band, the_member)
        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, the_member.name)

    def test_new_band_via_invite_email(self):
        the_band, the_member = self._create_test_band_with_member()
        goemail.send_new_band_via_invite_email(the_band, the_member)
        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, the_band.name)

    def test_gigo_invite_email(self):
        the_band, the_member = self._create_test_band_with_member()
        goemail.send_gigo_invite_email(the_band, the_member, self.TEST_URL)

        message = self._get_single_message()
        self.assertEqual(message.to, self.TEST_RECIPIENT)
        self.assertNotEmpty(message.subject)
        self.assertRegexpMatches(message.body.payload, self.TEST_BAND)
        self.assertRegexpMatches(message.body.payload, self.TEST_URL)

    def test_user_confirm_email(self):
        goemail.send_the_pending_email(self.TEST_RECIPIENT, self.TEST_URL)
        self.assertWellFormedAndContainsText(self.TEST_RECIPIENT, self.TEST_URL)

if __name__ == '__main__':
    unittest.main()