import uuid

from common.constants import PARENT_TYPE_DODD
from common.decorators import domain_celery_task
from podd.celery import app, DomainTask

from accounts.models import Authority

@app.task(base=DomainTask, bind=True)
@domain_celery_task
def create_podd_report_from_public_report(public_report_id):
    from reports.models import Report, AdministrationArea, ReportImage

    dodd_report = Report.objects.get(pk=public_report_id)
    if dodd_report.is_public and dodd_report.type.map_to:

        # find authority by report location
        dodd_location = dodd_report.report_location
        if not dodd_location:
            print "create_podd_report_from_public_report: Location not found"
            return

        authorities = Authority.objects.filter(area__covers=dodd_location)
        if authorities.count() <= 0:
            print "create_podd_report_from_public_report: Authority not found"
            return

        authority = authorities[0]
        print authority.id
        areas = AdministrationArea.objects.filter(authority=authority, name=authority.name)
        if not areas:
            print "create_podd_report_from_public_report: Default area of %s not found" % (authority.name,)
            return
        area = areas[0]
        podd_report = Report(
            domain=authority.domain,
            created_by=dodd_report.created_by,
            type=dodd_report.type.map_to,
            administration_area=area,
            negative=True,
            guid=str(uuid.uuid1()),
            report_id=0,
            incident_date=dodd_report.incident_date,
            date=dodd_report.date,
            form_data=dodd_report.form_data,
            report_location=dodd_location,
            rendered_form_data=dodd_report.rendered_form_data,
            administration_location=area.location,
            parent=dodd_report,
            parent_type=PARENT_TYPE_DODD,
            remark=''
        )
        podd_report.save()

        images = ReportImage.objects.filter(report=dodd_report)
        for image in images:
            tmp = ReportImage(
                report=podd_report,
                guid=image.guid,
                note=image.note,
                image_url=image.image_url,
                thumbnail_url=image.thumbnail_url,
                location=image.location,
                domain=image.domain
            )
            tmp.save()

    else:
        print("no map to found")