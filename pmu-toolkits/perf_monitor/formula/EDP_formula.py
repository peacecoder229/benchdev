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

from xml.etree import cElementTree as ET
from base import Formula, FormulaMap


class EDPMetric(Formula):
    """
    The object for EDP formulas. 
    
    decorator '@property' means we can call EDPMetric.desc() through 
        EDPMetric.desc
    """

    # todo: formulas include constant value will not be support by this version

    Body = None

    def __init__(self, metric):
        self.Body = metric
        self.set_alias(self.events)

    @property
    def desc(self):
        return self.Body.attrib["throughput-metric-name"]

    @property
    def name(self):
        return self.Body.attrib["name"]

    @property
    def formula(self):
        for element in self.Body:
            if element.tag == "formula":
                return element.text

    @property
    def events(self):
        event = []
        for element in self.Body:
            if element.tag == "event":
                event.append(element.text)
        return event

    @property
    def constant(self):
        event = []
        for element in self.Body:
            if element.tag == "constant":
                event.append(element.text)
        return event

    @property
    def Formula(self):
        # build a map 'covert' between alias and event counter name
        convert = {}
        for element in self.Body:
            # if element.tag in ("constant", "event"):
            if element.tag in ("event"):
                convert[element.attrib['alias']] = element.text
            else:
                continue

        formula = self.formula

        # 1st replacement, add {{ and }} around alias
        for char in convert.keys():
            formula = formula.replace(char, "{{%s}}" % char)

        # 2nd replacement, replace {{alias}} by event counter names
        for char in convert.keys():
            # char = "'%s'" % char
            formula = formula.replace("{{%s}}" % char, convert[char])

        return formula.lower()


class EDPFormulaReader:
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
        file_content = ET.ElementTree(file=filename)
        self.Content = file_content.getroot()

    def get_metric_list(self):
        """
        return all metrics 
        :return:  FormulaMap{<metrics name>: EDPMetric Object }
        """
        metrics = FormulaMap()
        for metric in self.Content:
            formula = EDPMetric(metric)
            metrics[formula.name.lower()] = formula

        return metrics
