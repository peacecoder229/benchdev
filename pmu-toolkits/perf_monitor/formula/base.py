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

class Formula:
    """
    The object which may create a run able calculator from str formulas
    """
    Formula = None
    alias = []
    name = "Unknown"

    def __init__(self, formula=None, alias=[]):
        """
        Initial object by a str, for example: formula = '(a+b) / c'
            alias = [a,b,c]

        :param formula: str
        :param alias: list aliases used by param 'formula'
        """
        self.Formula = formula
        self.set_alias(alias)

    def set_alias(self, alias):
        """
        sort alias by length

        :param alias: list
        :return: None
        """
        self.alias = sorted(alias, key=lambda a: 0 - len(a))

    def get_result(self, inputs):
        """
        input attributions by a dict, get the result for example:
        inputs = {"a":1, "b":3, "c": 2}

        return (1.0+3.0)/ 2.0 = 2.0

        :param inputs: dict
        :return: float
        """

        formula = self.Formula

        # Substitute values into the formula: (a+b) / c -> (1.0+3.0)/ 2.0
        for source in self.alias:
            source = source.lower()
            desc = str(float(inputs[source]))
            formula = formula.replace(source, desc)

        # calculate
        result = eval(formula)
        return result

    def __str__(self):
        return "%s = %s" % (self.name, self.Formula)


class FormulaMap:
    """
    Replacement of original dict
    """
    _cache = dict()

    def __setitem__(self, key, value):
        if key.startswith('__'):
            return
        key = key.lower()
        self._cache[key] = value
        self._cache[key[7:]] = value

    def __getitem__(self, item):
        item = item.lower().strip()

        if item.startswith('__') or item not in self._cache.keys():
            return None

        if item.startswith("metric_"):
            return self._cache[item[7:]]
        else:
            return self._cache[item]

    def __str__(self):
        return "\n".join([str(self._cache[k]) for k in self._cache.keys()])

    def __add__(self, other):
        self._cache = self._cache + other._cache
        return self
