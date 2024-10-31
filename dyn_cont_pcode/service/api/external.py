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

import time
from cache import Cache, CacheTransCode
from .base import BaseAPIServer
from ..transcation.strategy_view import StratergyViewController

__all__ = ["AllMetrics", "AllStrategies", "Strategy"]


class AllMetrics(BaseAPIServer):
    # todo: fake interface implemented.
    def get(self):
        data = {
            "PR": {"CPI": 1.0, "LLC_occupancy": 10240,
                   "LLC_misses": 1024, "CPU_frequency": 2000,
                   "bitway_setting": 11},
            "BE": {"CPI": 0.8, "LLC_occupancy": 10240,
                   "LLC_misses": 1024, "CPU_frequency": 2000,
                   "bitway_setting": 4},
        }

        self.response(data)


class AllStrategies(BaseAPIServer):
    trans_code = CacheTransCode.strategy_conf

    def get(self):
        cache = Cache()
        data = cache.get(self.trans_code)

        self.response(data)


class Strategy(BaseAPIServer):
    trans_code = CacheTransCode.strategy_conf

    def get(self, name):
        # read from cache and return back
        cache = Cache()
        data = cache.get(self.trans_code)
        if data is None or name not in data.keys():
            self.send_error(404)
            return

        self.response(data[name])

    def post(self, name):
        # strategy selection by url
        # todo: only 1 strategy can be used now
        if not name.endswith("model_based_round_roubin_controller"):
            self.send_error(404)
            return

        # validates json inputted
        request_body = self.get_request()
        keys = request_body.keys()
        if "target" not in keys or "configuration" not in keys:
            self.send_error(500)
            return
        request_body["update_timestamp"] = time.time()
        request_body["in_used"] = True

        # do real actions
        controller = StratergyViewController(request_body)
        controller.build_config()
        if not controller.change_strategy() :
            # throw out errors here
            self.send_error(505)
            return

        # write updates back to cache
        cache = Cache()
        setting = cache.get(self.trans_code)
        if setting is None:
            setting = {}

        setting[name] = request_body
        cache.set(self.trans_code, setting)

        self.response(request_body)
