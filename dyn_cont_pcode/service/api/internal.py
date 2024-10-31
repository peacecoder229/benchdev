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
import controller 
import json
from cache import Cache, CacheTransCode
from .base import BaseAPIServer
import time
from ..transcation.workload_view import Cmd2Action
import logging
CL = CL = logging.getLogger('closeloop')

__all__ = ["AllWorkloads", "Workloads"]

'''
class AllWorkloads(BaseAPIServer):
    def get(self, name=None):
        cache = Cache()
        workload_list = cache.get(CacheTransCode.workload)

        if name is None:
            data = workload_list

        else:
            if name not in workload_list.keys():
                self.send_error(404)
                return
            else:
                data = workload_list[name]

        self.response(data)

    def post(self, name):
        """
        Start a workload by json configurations

        :param name: str
        :return: None
        """
        request_body = self.get_request()
        cache = Cache()
        workload_list = cache.get(CacheTransCode.workload)

        if workload_list is None:
            workload_list = {}

        if name in workload_list.keys():
            pass
            # do stop
        request_body["start_time"] = time.time()
        workload_list[name] = request_body

        cache.set(CacheTransCode.workload, workload_list)

        self.response(request_body)

    def delete(self, name):
        """
        kill workloads by name

        :param name: str
        :return: None
        """
        pass
'''


class AllWorkloads(BaseAPIServer):
    def get(self, path):
        request = ["get_workload_waiting", "stop_workload",
                   "apply_for_workload"]

        if path not in request:
            self.send_error(404)
            return

        action = Cmd2Action(self.request.uri[9:])
        result = {"result": action.action()}

        self.response(result)

    def post(self, name):
        self.response("fake")


class Workloads(BaseAPIServer):
    def get(self, name):
        # read from cache and return back
        C = controller.get_controller()
        if name == "BE":
            data = C.get_BE()
        if name == "PR":
            data = C.get_PR()
        else:
            data = None
        if data is None:
            self.send_error(404)
            return
        self.response(data[name])

    def post(self, name):
        # validates json inputted
        request_body = json.loads(self.request.body)
        keys = request_body.keys()
        if "PID" not in keys or "name" not in keys:
            self.send_error(500)
            return
        C = controller.get_controller()
        if request_body["type"] == "PR":
            C.add_PR(request_body["name"], request_body["PID"])
        elif request_body["type"] == "BE":
            C.add_BE(request_body["name"], request_body["PID"])
        self.response(request_body)
