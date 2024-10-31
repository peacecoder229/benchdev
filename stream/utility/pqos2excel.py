#!/usr/bin/env python


import sys
import csv
import xlsxwriter
import commands

def read_file(filename):
    with open(filename, "r") as fd:
        return fd.readlines()


class ExcelMaker:
    DATA_SHEET = "data"
    CHART_SHEET = "charts"
    SUMMARY_SHEET = "summary"

    headers = {}

    def __init__(self, input, output, major_unit=None):
        self.major_unit = major_unit
        self.Input = input
        self.Output = xlsxwriter.Workbook(output)

    def finish(self):
        self.Output.close()

    def get_entries(self):
        for self.Length, entry in enumerate(self.Input):
            yield entry

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
                # pos = "%s%s" %(self.row_convert(self.Length+1), self.headers[k])

                date_sheet.write(self.Length + 1, self.headers[k], v)
                # date_sheet.write(pos, v)

        date_sheet.set_column('A:Z', 20)
        date_sheet.protect()

    def chart(self):
        chart_sheet = self.Output.add_chartsheet(self.CHART_SHEET)
        chart = self.Output.add_chart({'type': 'line'})
        for name, offset in self.headers.items():
            if name == "time":
                continue

            column = self.row_convert(offset)
            # Add a series to the chart.
            content = {
                'values': '=%s!$%s$2:$%s$%s' % (self.DATA_SHEET,
                                                column, column,
                                                self.Length + 2),
                'name': '=%s!$%s$1' % (self.DATA_SHEET,
                                       column)
            }
            chart.add_series(content)
            chart.set_x_axis({"visible": 0})

            if self.major_unit is not None:
                chart.set_y_axis({"major_unit": self.major_unit})

            # Insert the chart into the worksheet.
            # local = "AIQ"  # guess what's happened :)
            # pos = 1 + (offset // len(local)) * 15
            # pos = local[offset % len(local)] + str(pos)

            # chart.set_style(2)
            # chart.set_size(50)

            chart_sheet.set_chart(chart)

    def summary(self):
        summary_sheet = self.Output.add_worksheet(self.SUMMARY_SHEET)
        format = self.Output.add_format()
        format.set_bold()

        row = 0
        for fun in ("count", "sum", "average", "max", "min", "stdev"):
            row += 1
            summary_sheet.write(row, 0, fun, format)

            for i in self.headers.keys():
                if i == "time": continue

                summary_sheet.write(0, self.headers[i] + 1, i, format)
                column = self.row_convert(self.headers[i])
                formula = '=%s(%s!$%s$2:$%s$%s)' % (fun, self.DATA_SHEET,
                                                    column, column,
                                                    self.Length + 2)
                summary_sheet.write(row, self.headers[i] + 1, formula)


def put_to_csv(inputfile, csvfile):
    outfile = csvfile
    output = csv.writer(open(outfile, "w"), quoting=csv.QUOTE_NONNUMERIC)
    for line, row in enumerate(read_file(inputfile)):
        if (line % 4) is 0:
            time = row[5:-1]
        if line % 4 is 2:
            row = row.split()
            temp = row
            temp.insert(0, time)
        if line % 4 is 3:
            row = row.split()
            output.writerow(temp + row)


def read_csv_llc(inputfile):
    with open(inputfile, "r") as fd:
        reader = csv.reader(fd)
        for row in reader:
            tele = {
                "time": row[0],
                "Core%s_IPC" % row[1]: float(row[2]),
                "Core%s_IPC" % row[7]: float(row[8]),
                "Core%s_LLC" % row[1]: float(row[4]),
                "Core%s_LLC" % row[7]: float(row[10]),
                "Core%s_MB" % row[1]: float(row[6]) + float(row[5]),
                "Core%s_MB" % row[7]: float(row[12]) + float(row[11]),
             }
            yield tele


def read_csv_MBL(inputfile):
    with open(inputfile, "r") as fd:
        reader = csv.reader(fd)
        for row in reader:
            tele = {
                "time": row[0],
                "Core%s_MBL" % row[1]: float(row[5]),
                "Core%s_MBL" % row[7]: float(row[11]),
            }
            yield tele


def read_csv_MBR(inputfile):
    with open(inputfile, "r") as fd:
        reader = csv.reader(fd)
        for row in reader:
            tele = {
                "time": row[0],
                "Core%s_MBR" % row[1]: float(row[6]),
                "Core%s_MBR" % row[7]: float(row[12]),
            }
            yield tele


def read_csv_MB(inputfile):
    with open(inputfile, "r") as fd:
        reader = csv.reader(fd)
        for row in reader:
            tele = {
                "time": row[0],
                "Core%s_MB" % row[1]: float(row[6]) + float(row[5]),
                "Core%s_MB" % row[7]: float(row[12]) + float(row[11]),
            }
            yield tele


def make_excel(fun, filename, ax=None):
    exc = ExcelMaker(fun, filename + ".xlsx", ax)
    exc.save_entries()
    exc.summary()
    exc.chart()
    exc.finish()


def get_llc_size():
    cpuinfo = commands.getoutput("lscpu")
    fun = lambda s: int(s[s.find(":")+1:-1])
    for row in cpuinfo.split("\n"):
        if row.startswith("L2"):
            l2 = fun(row)
        if row.startswith("L3"):
            l3 = fun(row)
    if l2 == 1024:
        return l3 / 11
    return l3 / 20

if __name__ == "__main__":
    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = "mcf.out"
        output_file = "pqos"

    put_to_csv(input_file, output_file + ".csv")
    csv_file = output_file + ".csv"
    make_excel(read_csv_llc(csv_file), output_file + "_llc", get_llc_size())
    make_excel(read_csv_MBR(csv_file), output_file + "_mbr")
    make_excel(read_csv_MBL(csv_file), output_file + "_mbl")
#    make_excel(read_csv_MB(csv_file), output_file + "_mb")
