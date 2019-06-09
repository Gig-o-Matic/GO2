"""
Tools to help test the gig-o handlers etc.
"""
import band
import member

def make_test_member(name):
    (success, result1) = member.create_new_member('{0}@bar.com'.format(name), name, '12345')
    if not success:
        raise ValueError
    return result1


def make_test_band():
    return band.new_band("test band")


def make_test_handler(the_class, the_request_args={}, the_user=None):
    class Response:
        """ dummy response class """
        result = None
        headers = {}

        def write(self, result):
            self.result = result

        def clear(self):
            self.result = None

        def __str__(self):
            return "Response\n  Result:\n{0}\n\n  Headers:\n{1}".format(self.result, self.headers)

    class Request:
        """ dummy request class """
        args = {}
        url = 'http://localhost/'

        def get(self, arg, default):
            return self.args.get(arg, default)

    handler = the_class()
    handler.response = Response()

    handler.request = Request()
    handler.request.args = the_request_args

    handler.user = the_user

    return handler

