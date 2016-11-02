
import calendar
import json
import datetime

from django.http import HttpResponse

import xlwt



class VetReport:
    def __init__(self, report_type, reports, topic, subtopic=None):
        self.report_type = report_type
        self.reports = reports
        self.topic = topic
        self.subtopic = subtopic

        self.answers = {}

        self.run()

    def run(self):
        definition = json.loads(self.report_type.form_definition)

        questions = definition['questions']
        question = (item for item in questions if item['name'] == self.topic).next()

        items = question['items']

        if self.subtopic:

            subtopics = (item for item in questions if item['name'] == self.subtopic).next()
            subtopics = subtopics['items']

            for item in items:
                self.answers[item['id']] = item
                self.answers[item['id']]['subtopics'] = {}

                for sub in subtopics:
                    answers = {
                        1: 0,
                        2: 0,
                        3: 0,
                        4: 0,
                        5: 0,
                        6: 0,
                        7: 0,
                        8: 0,
                        9: 0,
                        10: 0,
                        11: 0,
                        12: 0,
                        'total': 0,
                    }
                    self.answers[item['id']]['subtopics'][sub['id']] = {
                        'id': sub['id'],
                        'text': sub['text'],
                        'answers': answers,
                    }

            for r in self.reports:
                data = json.loads(r.form_data)

                try:
                    values = data[self.topic].split(',')
                except:
                    print '%s not found in split.' % self.topic
                    values = []

                for value in values:
                    try:
                        self.answers[value]['subtopics'][data[self.subtopic]]['answers'][r.incident_date.month] += 1
                        self.answers[value]['subtopics'][data[self.subtopic]]['answers']['total'] += 1
                    except:
                        print '%s not found in loop.' % self.topic

        else:
            for item in items:
                item['answers'] = {
                    1: 0,
                    2: 0,
                    3: 0,
                    4: 0,
                    5: 0,
                    6: 0,
                    7: 0,
                    8: 0,
                    9: 0,
                    10: 0,
                    11: 0,
                    12: 0,
                    'total': 0,
                }
                self.answers[item['id']] = item

            for r in self.reports:
                data = json.loads(r.form_data)

                try:
                    values = data[self.topic].split(',')
                except:
                    print '%s not found in split.' % self.topic
                    values = []

                for value in values:
                    try:
                        self.answers[value]['answers'][r.incident_date.month] += 1
                        self.answers[value]['answers']['total'] += 1
                    except:
                        print '%s not found in loop.' % self.topic


class XlsSheet:
    def __init__(self, sheetname, header, data):
        self.data = data
        self.sheetname = sheetname
        self.header = header


class XlsRenderer:
    def __init__(self, filename):
        self.filename = filename
        self.sheets = []
        self.header_style = None

    def add_sheet(self, sheet):
        self.sheets.append(sheet)

    def write_sheet(self, wb, sheet):
        x = y = 0
        ws = wb.add_sheet(sheet.sheetname)

        min_header = 0
        for row in sheet.header:
            ws.write_merge(row[0], row[1], row[2], row[3], row[4], self.header_style)

            if row[1] > min_header:
                min_header = row[1]

        y = min_header + 1

        counter = 1
        for key, item in sheet.data.items():
            x = 0
            if item.has_key('text'):
                ws.write(y, x, counter)
                x += 1
                counter += 1

                ws.write(y, x, item['text'])

                if item.has_key('subtopics'):
                    y -= 1
                    for sub, sub_answer in item['subtopics'].items():
                        x = 2
                        y += 1
                        ws.write(y, x, sub_answer['text'])

                        for key, answer in sub_answer['answers'].items():
                            x += 1
                            ws.write(y, x, answer)

                else:
                    for key, answer in item['answers'].items():
                        x += 1
                        ws.write(y, x, answer)
            elif item.has_key('key'):
                key = item['key']
                for row in sheet.header:
                    ws.write(y, x, item['answers'][row[key]])
                    x += 1
            y += 1

    def run(self):
        wb = xlwt.Workbook()

        fnt = xlwt.Font()
        fnt.bold = True

        al = xlwt.Alignment()
        al.horz = xlwt.Alignment.HORZ_CENTER

        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1

        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']

        self.header_style = xlwt.XFStyle()
        self.header_style.font = fnt
        self.header_style.borders = borders
        self.header_style.pattern = pattern
        self.header_style.alignment = al

        for sheet in self.sheets:
            self.write_sheet(wb, sheet)

        response = HttpResponse(content_type="application/ms-excel")
        response['Content-Disposition'] = 'attachment; filename=%s.xls' % self.filename
        
        wb.save(response)
        return response


class ReportType:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.data = []
