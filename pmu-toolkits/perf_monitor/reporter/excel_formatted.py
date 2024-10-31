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

import xlsxwriter
from base import BaseReporter


class ExcelReporter(BaseReporter):
    DATA_SHEET = "data"
    CHART_SHEET = "charts"
    SUMMARY_SHEET = "summary"

    headers = {}

    def prepare(self):
        self.Output = xlsxwriter.Workbook("%s.xlsx" % self.Output)

    def row_convert(self, i):
        if i < 26:
            return chr(ord("A") + i)

        if i < 702:  # 26**2 + 26 = 702
            return self.row_convert(i // 26 - 1) + self.row_convert(i % 26)

        return self.row_convert(i // 702 - 1) + self.row_convert(i % 702 + 26)

    def save_entries(self):
        date_sheet = self.Output.add_worksheet(self.DATA_SHEET)
        for item in self.get_entries():
            if self.Length is 0:
                # add header, with bold fonts
                format = self.Output.add_format()
                format.set_bold()
                for idx, v in enumerate(item.keys()):
                    date_sheet.write(0, idx, v, format)
                    self.headers[v] = idx

            for k, v in item.items():
                date_sheet.write(self.Length + 1, self.headers[k], v)

    def teardown(self):
        self.chart()
        self.summary()

        self.Output.close()

    def chart(self):
        chart_sheet = self.Output.add_worksheet(self.CHART_SHEET)
        for i, offset in self.headers.items():
            name = i
            column = self.row_convert(offset)
            chart = self.Output.add_chart({'type': 'line'})
            # Add a series to the chart.
            content = {
                'values': '=%s!$%s$2:$%s$%s' % (self.DATA_SHEET,
                                                column, column,
                                                self.Length + 2),
                'name': name
            }
            chart.add_series(content)

            # Insert the chart into the worksheet.
            local = "AIQ"  # guess what's happened :)
            pos = 1 + (offset // len(local)) * 15
            pos = local[offset % len(local)] + str(pos)

            # chart.set_style(2)
            # chart.set_size(50)

            chart_sheet.insert_chart(pos, chart)

    def summary(self):
        summary_sheet = self.Output.add_worksheet(self.SUMMARY_SHEET)
        format = self.Output.add_format()
        format.set_bold()

        row = 0
        for fun in ("count", "sum", "average", "max", "min", "stdev"):
            row += 1
            summary_sheet.write(row, 0, fun, format)

            for i in self.headers.keys():
                summary_sheet.write(0, self.headers[i] + 1, i, format)
                column = self.row_convert(self.headers[i])
                formula = '=%s(%s!$%s$2:$%s$%s)' % (fun, self.DATA_SHEET,
                                                    column, column,
                                                    self.Length + 2)
                summary_sheet.write(row, self.headers[i] + 1, formula)


if __name__ == "__main__":
    import math


    def c():
        for i in xrange(-180, 180):
            if i is 0:
                continue

            yield {
                "dirct ratio ": 2 * i + 15,
                "square": i ** 2,
                "power": 2 ** i,
                "cube": i ** 3,
                "reciprocal": 18.0 / i,
                "e power": math.e ** i,
                "sin": math.sin(math.radians(i)),
                "tan": math.tan(math.radians(i)),
                "abs": abs(i)
            }


    c = ExcelReporter(c(), r"test")
