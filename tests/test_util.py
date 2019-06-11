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
        path = '/'

        def get(self, arg, default):
            return self.args.get(arg, default)

    class Auth:
        """ dummy auth class """
        def get_user_by_session(self):
            return True

    class User_Model:
        """ dummy user model """
        member = None

        def get_by_id(self,id):
            return self.member

    handler = the_class()
    handler.response = Response()

    handler.request = Request()
    handler.request.args = the_request_args

    handler.user_model = User_Model()
    handler.user_model.member = the_user

    handler.user = the_user
    handler.user_info = {'user_id':the_user.key.id() if the_user else None}
    handler.auth = Auth()

    return handler

