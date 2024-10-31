import csv
import sys


def read_result(filename):
    with open(filename, "r") as fd:
        for _ in range(3):
            fd.next()
        summary = []
        for count, row in enumerate(
                csv.reader(fd, delimiter=";", skipinitialspace=True)):
            summary.append(float(row[2]))

        average = sum(summary) / len(summary)
        summary = map(str, summary)
        return "run: %s, Iteration: %s, Median: %s, Values: %s" % (filename, len(summary), average, ",".join(summary))


if __name__ == "__main__":
    input_file = "score.txt"

    input_file = sys.argv[1]
    print (read_result(input_file))
