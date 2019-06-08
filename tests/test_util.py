"""
Tools to help test the gig-o handlers etc.
"""

def _make_test_handler(the_class):
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

    handler = the_class()
    handler.response = Response()
    return handler

