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
import re

from base import Formula
from base import FormulaMap


class PlainMetric(Formula):
    """
    The object for Plain formula.
    """

    Formula = None

    # keep this parameter for Monitors
    events = []

    def __init__(self, formula):
        eq_pos = formula.find("=")

        self.name = formula[:eq_pos]
        self.Formula = formula[eq_pos + 1:]
        self.alias = re.findall(r"[a-zA-Z\_\.]", self.Formula)

        self.events = self.alias


class PlainFormulaReader:
    """
    Factory class,
    Read EDP configuration files and covert XML contents to a metics list
    """
    Content = None

    def __init__(self, filename):
        """
        initial instances

        :param filename: EDP configuration file name
        """
        with open(filename, "r") as fd:
            content = fd.readlines()
        self.Content = content

    def get_metric_list(self):
        """
        return all metrics
        :return:  FormulaMap{<metrics name>: EDPMetric Object }
        """

        metrics = FormulaMap()
        for metric in self.Content:
            formula = PlainMetric(metric)
            metrics[formula.name] = formula

        return metrics