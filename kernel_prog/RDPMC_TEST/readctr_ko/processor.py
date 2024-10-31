class Counter:
    current = 0
    previous = 0
    MAX = (1 << 64) - 1

    def update(self, value):
        self.previous = self.current
        self.current = int(value)

        return self.value

    @property
    def value(self):
        if self.current < self.previous:
            return self.MAX - self.previous + self.current
        return self.current - self.previous


class Event:
    name = ""
    context = None

    def __init__(self, name="noname", width=100):
        self.name = name
        self.context = []

        for i in range(width):
            self.context.append(Counter())

    def update(self, vector):
        return [
            self.context[i].update(value) for i, value in enumerate(vector)]

    def __str__(self):
        values = [str(i.value) for i in self.context]
        return "%s\t%s" % (self.name, "\t".join(values))


class FileReader:
    def __init__(self, filename):
        self.fd = open(filename, "r")

    def __del__(self):
        self.fd.close()

    def readline(self):
        data = []
        while True:
            row = self.fd.readline()
            if row is None or len(row) is 0:
                break

            if row[1] == "-":
                yield data
                data = []
            else:
                metric = row.split()
                data.append(metric)

    def get_telemetry(self):
        tel = {}
        for t in self.readline():
            if t is None:
                return
            for row in t:
                name = row[0]
                if name not in tel.keys():
                    tel[name] = Event(name, len(row) - 1)
                tel[name].update(row[1:])
                print tel[name]

            print "-" * 6


if __name__ == "__main__":
    import sys
    filename = sys.argv[1]

    reader = FileReader(filename)
    reader.get_telemetry()
