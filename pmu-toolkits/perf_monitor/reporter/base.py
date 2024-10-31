#
# Copyright (c) 2017 by Intel Corp
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#


class BaseReporter:
    """
    The base class to implement reporters

    """

    Monitor = None
    Output = None
    Length = 0

    def __init__(self, monitor, output=None, auto_start=True):
        """
        save metrics into a csv file

        :param m: iterator
        :param output: filename | device description symb
        :param auto_start: bool, whether need to start the reporter directly.
        :return: None
        """
        self.Monitor = monitor
        self.Output = output

        if auto_start:
            self.start()

    def start(self):
        """
        Start record

        :return: None
        """
        self.prepare()

        # add try/finally to ensure the teardown method can be called any time
        try:
            self.save_entries()
        finally:
            self.teardown()

    def prepare(self):
        """
        Do something before save data

        :return: None
        """
        pass

    def get_entries(self):
        """
        get telemetries form monitor, set a counter to self.Length

        :return: iterator
        """
        for self.Length, telemetry in enumerate(self.Monitor):
            yield telemetry

    def save_entries(self):
        """
        Main function for save contents.

        :return: None
        """
        pass

    def teardown(self):
        """
        Do something after saving finished.

        :return: None
        """
        pass

    def __len__(self):
        """
        The counter for entries

        :return: int
        """
        return self.Length
