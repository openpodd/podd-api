import calendar
import json
import datetime
import math


class Area:
    def __init__(self, id, name, parent_name, address, location):
        self.id = id
        self.name = name
        self.parentName = parent_name 
        if location:
            self.location = json.loads(location)
        else:
            self.location = ''
        self.address = address
        self.positiveReport = 0
        self.negativeReport = 0
        self.totalReport = 0
        self.reporters = []

    def put_reporter(self, reporter):
        self.reporters.append(reporter)
        self.totalReport += reporter.totalReport
        self.positiveReport += reporter.positiveReport
        self.negativeReport += reporter.negativeReport


class AreaDate(Area):
    def __init__(self, id, name, parent_name, address, location, dates):
        Area.__init__(self, id, name, parent_name, address, location)
        self.dates = []
        self.negativeReport = 0
        self.positiveReport = 0
        self.totalReport = 0
        for date in dates:
            self.dates.append(Date(date=date))

    def put_reporter(self, reporter):
        Area.put_reporter(self, reporter)
        
        for index, date in enumerate(reporter.dates):
            self.dates[index].count_from_reporter(date.total, date.negative, date.positive)

    def put_report(self, report_negative, report_date):
        for date in self.dates:
            if date.date == report_date:
                date.count_from_report(report_negative)

        if report_negative:
            self.negativeReport += 1
        else:
            self.positiveReport += 1
        self.totalReport += 1


class AreaDetail(Area):
    def __init__(self, id, name, parent_name, address, location, report_types, time_ranges):
        Area.__init__(self, id, name, parent_name, address, location)
        self.reportTypes = []
        self.animalTypes = []
        self.timeRanges = []
        self.countDayReport = 0
        self.grade = ''

        for report_type in report_types:
            self.reportTypes.append(ReportType(id=report_type.id, name=report_type.name))

        for time_range in time_ranges:
            self.timeRanges.append(TimeRange(start_time=time_range['startTime'], end_time=time_range['endTime']))

    def set_grade(self, grade):
        self.grade = grade

    def put_reporter(self, reporter):
        Area.put_reporter(self, reporter)
        
        for index, report_type in enumerate(reporter.reportTypes):
            self.reportTypes[index].count_from_reporter(report_type.totalReport)

        for index, time_range in enumerate(reporter.timeRanges):
            self.timeRanges[index].count_from_reporter(time_range.totalReport)

        for index, reporter_animal_type in enumerate(reporter.animalTypes):
            find_animal_type = False
            for animal_type in self.animalTypes:
                if animal_type.name == reporter_animal_type.name:
                    find_animal_type = True
                    animal_type.count_animal_type(reporter_animal_type.sick, 
                        reporter_animal_type.death, reporter_animal_type.total, 
                        reporter_animal_type.nearBy
                    )

            if not find_animal_type:
                animal_type = AnimalType(name=reporter_animal_type.name)
                animal_type.count_animal_type(reporter_animal_type.sick, 
                    reporter_animal_type.death, reporter_animal_type.total, 
                    reporter_animal_type.nearBy
                )
                self.animalTypes.append(animal_type)

        ########## Count report day from all reporter ######################
        self.countDayReport += len(reporter.dateReports)


class Reporter:
    def __init__(self, id, full_name, status, thumbnail_avatar_url, administration_area):
        self.id = id
        self.fullName = full_name
        self.status = status
        self.thumbnailAvatarUrl = thumbnail_avatar_url
        self.administrationArea = administration_area
        self.positiveReport = 0
        self.negativeReport = 0
        self.totalReport = 0

    def put_report(self, report_negative):
        if report_negative:
            self.negativeReport += 1
        else:
            self.positiveReport += 1
        self.totalReport += 1 


class ReporterDate(Reporter):
    def __init__(self, id, full_name, status, thumbnail_avatar_url, administration_area, dates):
        Reporter.__init__(self, id, full_name, status, thumbnail_avatar_url, administration_area)
        self.dates = []
        for date in dates:
            self.dates.append(Date(date=date))

    def put_report(self, report_negative, report_date):
        Reporter.put_report(self, report_negative)
        for date in self.dates:
            if date.date == report_date:
                date.count_from_report(report_negative)


class ReporterDetail(Reporter):
    def __init__(self, id, full_name, status, thumbnail_avatar_url, administration_area, report_types, time_ranges):
        Reporter.__init__(self, id, full_name, status, thumbnail_avatar_url, administration_area)
        self.reportTypes = []
        self.animalTypes = []
        self.timeRanges = []
        self.dateReports = []

        for report_type in report_types:
            self.reportTypes.append(ReportType(id=report_type.id, name=report_type.name))

        for time_range in time_ranges:
            self.timeRanges.append(TimeRange(start_time=time_range['startTime'], end_time=time_range['endTime']))

    def put_report(self, report_negative, type, report_animal_type, report_date, created_by_hour):
        Reporter.put_report(self, report_negative)
        
        for report_type in self.reportTypes:
            if report_type.id == type:
                report_type.count_from_report()

        for time_range in self.timeRanges:
            if (time_range.startTime <= created_by_hour and time_range.endTime > created_by_hour) or\
            (time_range.startTime > time_range.endTime and (time_range.startTime <= created_by_hour or time_range.endTime > created_by_hour)):
                time_range.count_from_report()

        if report_animal_type:
            find_animal_type = False
            for animal_type in self.animalTypes:
                if animal_type.name == report_animal_type['name']:
                    find_animal_type = True
                    animal_type.count_animal_type(report_animal_type['sick'], 
                        report_animal_type['death'], report_animal_type['total'], 
                        report_animal_type['nearBy']
                    )
            
            if not find_animal_type:
                animal_type = AnimalType(name=report_animal_type['name'])
                animal_type.count_animal_type(report_animal_type['sick'], 
                    report_animal_type['death'], report_animal_type['total'], 
                    report_animal_type['nearBy']
                )
                self.animalTypes.append(animal_type)

        if report_date:
            find_date = False
            for date in self.dateReports:
                if date == report_date:
                    find_date = True
            
            if not find_date:
                self.dateReports.append(report_date)

class Date:
    def __init__(self, date):
        week = list(calendar.day_name)
        self.date = date.strftime('%d-%m-%Y')
        self.dayOfWeek = week[date.weekday()]
        self.total = 0
        self.negative = 0
        self.positive = 0

    def count_from_report(self, negative):
        if negative:
            self.negative += 1
        else:
            self.positive += 1
        self.total += 1 

    def count_from_reporter(self, total, negative, positive):
        self.negative += negative
        self.positive += positive
        self.total += total 


class TimeRange:
    def __init__(self, start_time, end_time):
        self.startTime = start_time
        self.endTime = end_time
        self.totalReport = 0
    
    def count_from_report(self):
        self.totalReport += 1

    def count_from_reporter(self, total_report):
        self.totalReport += total_report


class ReportType:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.totalReport = 0
    
    def count_from_report(self):
        self.totalReport += 1

    def count_from_reporter(self, total_report):
        self.totalReport += total_report


class AnimalType:
    def __init__(self, name):
        self.name = name
        self.sick = 0
        self.death = 0
        self.total = 0
        self.nearBy = 0

    def count_animal_type(self, sick, death, total, near_by):
        if sick:
            self.sick += int(sick)

        if death:
            self.death += int(death)

        if total:
            self.total += int(total)

        if near_by:
            self.nearBy += int(near_by)


class ComputeGrade:
    def __init__(self, scores, grades, N):
        self.scores = scores
        self.grades = grades

        self.mean =  (sum(scores) * 1.0) / (N * 1.0) if N else 0
        variance = 0
        for score in self.scores:
            variance += ((score - self.mean) ** 2)
        
        self.variance = variance / (N * 1.0) if N else 0
        self.std = math.sqrt(self.variance)

    def score_to_grade(self, score):
        if self.std == 0:
            if self.mean == 0:
                return 'no grade'
            else:
                return self.grade[0]
        else:    
            zscore = (float(score) - self.mean) / self.std
            tscore = (zscore * 10.0) + 50.0
            for grade in self.grades:
                if tscore > grade['tScore']:
                    return grade['name']


class ReportTypeTemplate:
    def __init__(self, id, name, template):
        self.id = id
        self.name = name
        self.template = template

    def get_template(self):
        return self.template


class MonthlyReporter:
    def __init__(self, name, dates):
        self.name = name
        self.total = 0
        self.dates = []
        # for date in dates:
        #     self.dates[date.strftime('%d-%m-%Y')] = ''


class DateReport:
    def __init__(self, date):
        self.date = date.strftime('%d-%m-%Y')
        self.total = 0
