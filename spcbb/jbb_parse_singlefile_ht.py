import csv
import os
import sys

from DataReader.SPECjbb import SPECjbb2015TotalPurchaseData


class Result:
    data = []
    header = ["run_mode", "hpcore", "IR", "P50", "P90", "P95", "P99", "cat", "mba",  "lpcore"]

    root_path = ""
    sigma = 4.0

    def __init__(self, path, tag):
        self.root_path = path
        self.data = [None] * len(self.header)

        tag = tag.replace("_", "-").split("-")
        self.data[0] = tag[0][0:1].lower()
        self.data[1] = int(tag[0][2:])
        self.data[2] = int(tag[8][2:])
        self.data[7] = tag[2][3:]
        self.data[8] = tag[3][2:]
        self.data[9] = int(tag[1][1:])

    def get_specjbb_result(self):
        if self.data[0] == "c":
            f = "composite.out"
        elif self.data[0] == "m":
            f = "controller.out"
#SPECjbb2015TotalPurchaseData search for TotalPurchase pattern and then taken the whole line which has info on Success, p50 etc from the logout file
        reader = SPECjbb2015TotalPurchaseData(os.path.join(self.root_path, f))

        data = reader.all
        #start of filtering
        #print(data["p50"])
        #below filtering objects are defined. For each of these elements
        #dataframe is filtered to only have the rows where corresponding objects such as p95 lies within the Bound defined by
        # avg +/- 2*std
        #print(data)
        flt = ["p50", "p90", "p90", "p90", "p95", "p95", "p95", "p99", "p99", "p99"]
        for i in range(len(flt)):
            #print("Filtering outlier in " + flt[i])
            avg = data[flt[i]].mean()
            std = data[flt[i]].std()
            outlier = avg + self.sigma / 2 * std
        #print(avg, std, outlier)
        #print(data["p50"])
            #print(data)
        # below line creates a subset of dataframes where p50 is not greater than 2 times std deviation and not less than two time std deviation
            data = data[data[flt[i]] >= (avg - self.sigma / 2 * std)]
            data = data[data[flt[i]] <= (avg + self.sigma / 2 * std)]
        #print("After processing")
        #print(data)
        #one more filtering

        #print("After processing")
            #print(data)

        #End of filtering

        self.data[3] = data["p50"].mean()
        self.data[4] = data["p90"].mean()
        self.data[5] = data["p95"].mean()
        self.data[6] = data["p99"].mean()

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


def file_walk(root_path):
        path = os.getcwd()
        tag = root_path
        #print(path)
        reader = Result(path, tag)
        #print(path + "   " + tag)
        reader.get_specjbb_result()
        #print(reader.to_dict())
        return reader.to_dict()
def main(root_path):
    writer = csv.DictWriter(sys.stdout, fieldnames=Result.header)
    writer.writeheader()
    writer.writerow(file_walk(root_path))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = r"."

    main(root)
