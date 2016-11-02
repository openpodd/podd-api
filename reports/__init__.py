import json

class Area:
    def __init__(self, id, name, address, location):
        self.id = id
        self.name = name
        self.address = address
        self.location = location
        self.positive = 0
        self.negative = 0
        self.positiveCases = []
        self.negativeCases = []

    def put_report_case(self, report):
        if report.negative:
            self.negativeCases.append(report)
            self.negative += 1
        else:
            self.positiveCases.append(report)
            self.positive += 1
