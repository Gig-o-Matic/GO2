# Code based on ReSTify
# ReST interface for appengine
#
# ReSTify is a ready to deploy Rest interfae for your appengine datastore for testing purposes.
#
# Copyright 2013 Mevin Babu Chirayath <mevinbabuc@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Heavily modified by Aaron Oppenheimer
#

import os
import sys

from google.appengine.api import users

import webapp2
import json

# from go2jwt import *


# Add the URL of the site requesting the ReST server i.e. origin of request to the ReST server*/
ORIGIN_SITE_NAME = "http://example.com"

def rest_user_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        user = self.user
        if user is None:
            raise gigoexceptions.GigoRestException('rest api hit without user')
        else:
            return handler(self, *args, **kwargs)

    return check_login
    # return handler

def CSOR_Jsonify(func):
    """ decorator to make all requests CSOR compatible and jsonfy the output """

    def wrapper(*args, **kw):

        def datetimeconvert(obj):
            """datetimeconvert JSON serializer."""
            
            import datetime

            if isinstance(obj, datetime.datetime):
                return obj.strftime("%Y/%m/%d %H:%M")

            return str(obj)

        dataObject=func(*args, **kw)

        try:
            _origin = args[0].request.headers['Origin']
        except:
            _origin = ORIGIN_SITE_NAME

        args[0].response.headers.add_header("Access-Control-Allow-Origin", _origin)
        args[0].response.headers.add_header("Access-Control-Allow-Credentials", "true")
        args[0].response.headers.add_header("Access-Control-Allow-Headers",
         "origin, x-requested-with, content-type, accept")
        args[0].response.headers.add_header('Content-Type', 'application/json')

        if dataObject:
            args[0].response.write(json.dumps(dataObject, default = datetimeconvert))

    return wrapper

