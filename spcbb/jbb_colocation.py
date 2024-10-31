import csv
import os
import sys

from DataReader.SPECjbb import SPECjbb2015TotalPurchaseData


class Result:
    data = []
    header = ["run_mode", "core_count", "IR", "P50", "P90", "P95", "P99"]

    root_path = ""
    sigma = 4.0

    def __init__(self, path, tag):
        self.root_path = path
        self.data = [None] * len(self.header)

        tag = tag.replace("_", "-").split("-")
        self.data[0] = tag[0][0].lower()
        self.data[1] = int(tag[0][1:])
        self.data[2] = int(tag[1][2:])

    def get_specjbb_result(self):
        if self.data[0] == "c":
            f = "composite.out"
        elif self.data[0] == "m":
            f = "controller.out"
#SPECjbb2015TotalPurchaseData search for TotalPurchase pattern and then taken the whole line which has info on Success, p50 etc from the logout file
        reader = SPECjbb2015TotalPurchaseData(os.path.join(self.root_path, f))

        data = reader.all
        #print(data["p50"])
        avg = data["p50"].mean()
        std = data["p50"].std()
        outlier = avg + self.sigma / 2 * std
        #print(avg, std, outlier)
        #print(data)
        # below line creates a subset of dataframes where p50 is not greater than 2 times std deviation and not less than two time std deviation
        data = data[data["p50"] >= (avg - self.sigma / 2 * std)]
        data = data[data["p50"] <= (avg + self.sigma / 2 * std)]
        #print("After processing")
        #print(data)
        self.data[3] = data["p50"].mean()
        self.data[4] = data["p90"].mean()
        self.data[5] = data["p95"].mean()
        self.data[6] = data["p90"].mean()

    def to_dict(self):
        return dict(zip(self.header, self.data))
    # Above zip creates list of tuples from two lists
    # Then dict creates a dic from list of tuples. So now every data will be a value  for the correspoding
    #key defined by the header


def path_walk(root_path):
    for tag in os.listdir(root_path):
        path = os.path.join(root_path, tag)
        if not os.path.isdir(path):
            continue

        reader = Result(path, tag)
        #print(path + "   " + tag)
        reader.get_specjbb_result()
        yield reader.to_dict()


def main(root_path):
    writer = csv.DictWriter(sys.stdout, fieldnames=Result.header)
    writer.writeheader()
    for entry in path_walk(root_path):
        #print(entry)
        writer.writerow(entry)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = r"."

    main(root)
