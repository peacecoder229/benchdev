#
#  Copyright (c) 2018 by Intel Corp
#  All rights reserved.
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use,
#  copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following
#  conditions:
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#

import tornado.web
import json

SERVER_NAME = "Dynamic_resource_controller/ver1.0"


class BaseAPIServer(tornado.web.RequestHandler):
    def set_default_headers(self):
        """
        Redirect server names
        :return: None
        """
        self.set_header("Server", SERVER_NAME)

    def get_request(self, json_decode=True):
        """
        return request body by dict object

        :param json_decode: boolean
        :return:  dict
        """
        if json_decode:
            return json.loads(self.request.body)

        return self.request.body

    def response(self, data, json_encode=True):
        """
        send api results

        :param data: dict
        :param json_encode: boolean
        :return: None
        """
        if json_encode:
            data = json.dumps(data)

        self.finish(data)
