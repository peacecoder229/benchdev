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

import tornado.ioloop
import tornado.web
from threading import Thread
from service.api.external import *
from service.api.internal import *

INTERNAL_API_PORT = 2017
EXTERNAL_API_PORT = 2018


def start_api():
    internal_api_router = [
        (r"/workloads/", AllWorkloads),
        (r"/workload/(.*)", Workloads),
    ]

    external_api_router = [
        (r"/metrics/", AllMetrics),
        (r"/strategies/", AllStrategies),
        (r"/strategy/(.*)", Strategy),

        # static web pages
        # (r"/(.*)", tornado.web.StaticFileHandler,
        #  {"path": "assets", "default_filename": "index.html"}),
    ]

    internal_api = tornado.web.Application(internal_api_router)
    external_api = tornado.web.Application(external_api_router)

    internal_api.listen(INTERNAL_API_PORT)
    external_api.listen(EXTERNAL_API_PORT)

    tornado.ioloop.IOLoop.instance().start()


def start_api_thread():
    thread = Thread(target=start_api)
    thread.start()


if __name__ == "__main__":
    start_api()
