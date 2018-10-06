# ReSTify
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

__author__ = 'mevinbabuc@gmail.com (Mevin Babu Chirayath)'
__version__ = "0.1"

import os
import sys

from google.appengine.api import users
from webapp2_extras.auth import *
from requestmodel import *
from webapp2_extras.appengine.auth.models import UserToken
from webapp2_extras.appengine.auth.models import User
import base64

import webapp2
import json

from go2jwt import *

from model import *
import settings

def get_model_from_URL(node_name):
    
    # Get the corresponding model name from URL
    model_alias = settings.MODEL_NAME_ALIAS[node_name]
    return getattr(model, model_alias)

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
            _origin = settings.ORIGIN_SITE_NAME

        args[0].response.headers.add_header("Access-Control-Allow-Origin", _origin)
        args[0].response.headers.add_header("Access-Control-Allow-Credentials", "true")
        args[0].response.headers.add_header("Access-Control-Allow-Headers",
         "origin, x-requested-with, content-type, accept")
        args[0].response.headers.add_header('Content-Type', 'application/json')

        if dataObject:
            args[0].response.write(json.dumps(dataObject, default = datetimeconvert))

    return wrapper

class ReST(webapp2.RequestHandler):
    """ Class to handle requests (GET, POST, DELETE, PUT) to the route /api/ """


    @CSOR_Jsonify
    def post(self,query=""):
        """Post Request handler to add data to the datastore

        Args:

        return:
            A status object which contains the data added and error messages if any.
            status['object']
            status['success']
            status['error']

        response status codes :
            201 -> Created   -> When a new object is succesfully saved in the datastore
            404 -> Not Found -> When the post body is invalid or null

        """

        status={}
        status["error"]=None
        status["success"]=True
        key=False
        json_args_dic = None

        node = self.request.path_info.split('/')
        if node[-1] == '':
            node.pop(-1)

        _model = get_model_from_URL(node[2])

        _json = self.request.body.encode("utf-8")

        try:
            json_args_dic = json.loads(_json,encoding="utf-8")
        except:
            json_args_dic = None
            self.abort(400)

        if json_args_dic:
            HashEntry=_model(author=users.get_current_user(), **json_args_dic)
            key=HashEntry.put()
            self.response.set_status(201,"Created")

            json_args_dic['id'] = key.id()
            status['object'] = json_args_dic

        if not key:
            status["success"] = False
            status["error"] = "Unable to Add your Tab.Try again"
            self.abort(404)

        return status

    @CSOR_Jsonify
    def get(self,query=""):
        """Get request handler to retrieve data from datastore

        Args:

        Return:
            An object containing all the entities of the logged in user.

        Response status codes :
            404 -> Not Found -> When there's no data in the datastore for the
                                particular user
            400 -> Bad Request->When the program is unable to search db etc.
                                Try again later.
            200 -> Ok -> When data is found and proper data is returned.

        """

        try:
            token = self.request.headers['Authorization']
            userkey = token[8:][:-1]
            print(userkey)
            user = decode_jwt(userkey)
            print(user)
        except:
            self.abort(401)

        qry = None
        Object_by_id = None
        _model = None

        node = self.request.path_info.split('/')

        if node[-1] == '':
            node.pop(-1)

        if len(node) - 1 >= 2:
            if node[2]:
                try:
                    _model = get_model_from_URL(node[2])
                except:
                    _model = None

            if len(node) -1 > 2 and _model:
                # Object_by_id = _model.get_by_id(int(node[3]))
                Object_by_id = ndb.Key(urlsafe=node[3]).get()
            elif node[2] and _model:
                qry = _model.query().filter(_model.author == users.get_current_user())
            else:
                print str(_model)
                self.abort(404)

        dataList=[]

        if qry :
            for temp in qry:
                dataObject=temp.to_dict()
                dataObject["id"] = temp.key.id()
                dataList.append(dataObject)

        elif Object_by_id:
            # only expose the pieces we want to expose
            if node[2] in settings.MODEL_EXPOSE.keys():
                dataObject=Object_by_id.to_dict(include=settings.MODEL_EXPOSE[node[2]])
            else:
                dataObject=Object_by_id.to_dict()

            # if anything in the object is an ndb.Key, send back the urlsafe key instead
            for k in dataObject.keys():
                if type(dataObject[k])==ndb.Key:
                    d = dataObject[k].urlsafe()
                    dataObject[k]=d

            dataList.append(dataObject)

        if len(dataList)==0:
            self.abort(404)
            dataList = None
        elif not qry and not Object_by_id:
            self.abort(400)
        else :
            self.response.set_status(200,"Ok")

        return dataList

    @CSOR_Jsonify
    def delete(self,query=""):
        """Delete request handler to delete an entity from datastore

        Args:

        Return:
            Delete request is not supposed to return any value

        Response status codes :
            404 -> Not Found -> When the data to be deleted is not found
            204 -> No Content-> When data is found in the datastore and deleted,
                                so there's no content to return
            400 -> Bad Request->When invalid delete request was made

        """

        Object_by_id = None
        _model = None

        node = self.request.path_info.split('/')
        if node[-1] == '':
            node.pop(-1)

        if len(node) - 1 > 2:
            if node[2]:
                try:
                    _model = get_model_from_URL(node[2])
                except:
                    _model = None

            if _model:
                Object_by_id = _model.get_by_id(int(node[3]))
        else:
            self.abort(404)

        if Object_by_id:
            Object_by_id.key.delete()
            self.response.set_status(204,"No Content")
        elif not _model:
            self.abort(404)
        else:
            self.abort(400)

        return {}

    @CSOR_Jsonify
    def put(self,query=""):
        """PUT request handler to edit an entity from datastore

        Args:

        Return:
            returns the edited object

        Response status codes :
            404 -> Not Found -> When the data to be deleted is not found in the 
                                datastore
            200 -> Ok        -> When data is found in the datastore and edited
            400 -> Bad Request->When invalid id or model name was used to make 
                                put request

        """
        status={}
        status["error"]=None
        status["success"]=True
        Object_by_id = None
        _model = None
        _json = None
        json_args_dic = None
        HashEntry = None

        node = self.request.path_info.split('/')
        if node[-1] == '':
            node.pop(-1)

        if len(node) - 1 > 2:
            if node[2]:
                try:
                    _model = get_model_from_URL(node[2])
                except:
                    _model = None

            #check if the id is a valid one
            if _model:
                Object_by_id = _model.get_by_id(int(node[3]))
            else:
                self.abort(404)

            # if data already present in server, then modify
            if Object_by_id:
                _json = self.request.body.encode("utf-8")

                try:
                    json_args_dic = json.loads(_json,encoding="utf-8")
                except:
                    json_args_dic = None

                if json_args_dic :
                    json_args_dic["id"]=int(node[3])
                    status['object'] = json_args_dic
                    HashEntry=_model(author=users.get_current_user(), **json_args_dic)
                    key=HashEntry.put()
                else:
                    self.abort(400)
            else:
                self.abort(404)
        else:
            self.abort(404)

        if HashEntry:
            self.response.set_status(200,"Ok")
            return status
        else:
            self.abort(404)

    def options(self,query=""):

        try:
            _origin = self.request.headers['Origin']
        except:
            _origin = settings.ORIGIN_SITE_NAME

        self.response.set_status(200,"Ok")
        self.response.headers.add_header("Access-Control-Allow-Origin", _origin)
        self.response.headers.add_header("Access-Control-Allow-Methods",
         "GET, POST, OPTIONS, PUT, DELETE")
        self.response.headers.add_header("Access-Control-Allow-Credentials", "true")
        self.response.headers.add_header("Access-Control-Allow-Headers",
         "origin, x-requested-with, content-type, accept")


class Auth(BaseHandler):
    @CSOR_Jsonify
    def post(self,query=""):
        email = self.request.get('email').lower()
        password = self.request.get('password')

        try:
            u = self.auth.get_user_by_password(email, password, save_session=True)
            the_user = self.user_model.get_by_id(u['user_id'])

        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.abort(401)

        jwt = make_jwt(the_user.key.urlsafe())

        return jwt

