# -*- encoding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import User, Authority
from common.constants import GROUP_WORKING_TYPE_ADMINSTRATION_AREA
from common.decorators import superuser_required
from logs.functions import list_for_content_type, list_for_object, list_for_user
from reports.models import AdministrationArea, Report, ReportInvestigation, ReportLaboratoryCase, AnimalLaboratoryCause, \
                           AnimalLaboratoryCause
from reports.serializers import AnimalLaboratoryCauseSerializer
from supervisors.forms import SupervisorsUserForm, SupervisorsAuthorityForm, SupervisorsReportInvestigationForm, \
                              SupervisorsReportLaboratoryCaseForm
from supervisors.functions import (get_querystring_filter_user_status, 
    export_excel_users_to_create_authorities,
    import_authorities_excel, import_and_excel_users_to_create_authorities,
    print_invite_code_authorities)


@login_required
@superuser_required
def supervisors_home(request):
    return redirect('supervisors_users')


@login_required
# @superuser_required
def supervisors_users(request):
    if request.user.is_superuser:
        return redirect('supervisors_users_by_status', user_status='volunteer')

    return redirect('supervisors_report_investigation')

    # return render(request, 'supervisors/supervisors_users_list.html', {
    #     'areas': AdministrationArea.get_root_nodes(),
    #     'status': 'users',
    # })


@login_required
@superuser_required
def supervisors_users_by_status(request, user_status):
    if user_status not in ['volunteer', 'podd', 'livestock', 'public-health', 'additional-volunteer', 'additional-volunteer-dodd']:
        raise Http404

    querystring = get_querystring_filter_user_status({}, user_status)
    return render(request, 'supervisors/supervisors_users_list.html', {
        'status': user_status,
        'users': User.objects.filter(**querystring).order_by('username'),
    })


def supervisors_export_users_excel_to_authorities(request):
    return export_excel_users_to_create_authorities()

@login_required
@superuser_required
def supervisors_authorities(request):
    success = None
    error = None
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            success = import_authorities_excel(file)
            if success:
                messages.success(request, u'สร้างองค์กรใหม่สำเร็จ')
            else:
                messages.error(request, u'ไม่สามารถสร้างองค์กรใหม่สำเร็จ ไฟล์ไม่ถูกต้อง')

    return render(request, 'supervisors/supervisors_authorities_list.html', {
            'authorities': Authority.objects.order_by('code'),
        })


@login_required
@superuser_required
def supervisors_new_authorities(request):
    response = {}
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            return import_and_excel_users_to_create_authorities(file)

    return HttpResponse('False')


@login_required
@superuser_required
def supervisors_authorities_print_invitation_code(request):
    return print_invite_code_authorities()


@login_required
@superuser_required
def supervisors_authorities_edit(request, authority_id):
    authority = get_object_or_404(Authority, id=authority_id)

    if request.method == 'POST':
        form = SupervisorsAuthorityForm(request.POST, instance=authority)
        if form.is_valid():
            form.save()
            messages.success(request, u'แก้ไขข้อมูลเรียบร้อยแล้ว')
    else:
        form = SupervisorsAuthorityForm(instance=authority)

    return render(request, 'supervisors/supervisors_authorities_form.html', {
        'authority': authority,
        'form': form,
    })

@login_required
@superuser_required
def supervisors_users_by_area(request, area_id):
    return redirect('supervisors_users_by_area_and_status', user_status='volunteer', area_id=area_id)
    # area = get_object_or_404(AdministrationArea, id=area_id)
    # return render(request, 'supervisors/supervisors_users_list.html', {
    #     'areas': [area],
    #     'selected_area': area,
    #     'status': 'users',
    # })


@login_required
@superuser_required
def supervisors_users_by_area_and_status(request, user_status, area_id):
    if user_status not in ['volunteer', 'podd', 'livestock', 'public-health']:
        raise Http404

    area = get_object_or_404(AdministrationArea, id=area_id)

    querystring = {
        'groups__groupadministrationarea__administration_area': area,
        'groups__type': GROUP_WORKING_TYPE_ADMINSTRATION_AREA,
    }
    querystring = get_querystring_filter_user_status(querystring, user_status)
    return render(request, 'supervisors/supervisors_users_list.html', {
        'areas': [area],
        'selected_area': area,
        'status': user_status,
        'users': User.objects.filter(**querystring).order_by('username'),
    })


@login_required
@superuser_required
def supervisors_users_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = SupervisorsUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save(created_by=request.user)
            messages.success(request, u'แก้ไขข้อมูลเรียบร้อยแล้ว')
    else:
        form = SupervisorsUserForm(instance=user)

    return render(request, 'supervisors/supervisors_users_form.html', {
        'user': user,
        'form': form,
    })


@login_required
@superuser_required
def supervisors_logs_reports(request):
    logs = list_for_content_type(Report)
    paginator = Paginator(logs, 25)

    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logs = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_logs_reports.html', {
        'logs': logs
    })


@login_required
@superuser_required
def supervisors_logs_reports_by_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    logs = list_for_object(report)
    paginator = Paginator(logs, 25)

    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logs = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_logs_reports.html', {
        'logs': logs,
        'item': report,
        'log_header': u'Report #%d' % report.id,
    })


@login_required
@superuser_required
def supervisors_logs_reports_by_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    logs = list_for_user(user)
    paginator = Paginator(logs, 25)

    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logs = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_logs_reports.html', {
        'logs': logs,
        'item': user,
        'log_header': u'User %s' % user.username,
    })


@login_required
@superuser_required
def supervisors_logs_users(request):
    logs = list_for_content_type(User)
    paginator = Paginator(logs, 25)

    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logs = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_logs_users.html', {
        'logs': logs
    })


@login_required
@superuser_required
def supervisors_logs_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    logs = list_for_object(user)
    paginator = Paginator(logs, 25)

    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        logs = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_logs_users.html', {
        'logs': logs,
        'item': user,
        'log_header': u'%s' % user.username,
    })


@login_required
# @superuser_required
def supervisors_report_investigation_create(request):

    if request.method == 'POST':
        form = SupervisorsReportInvestigationForm(request.POST, request.FILES)
        if form.is_valid():
            investigation = ReportInvestigation(
                domain=form.cleaned_data['report'].domain,
                report=form.cleaned_data['report'],
                note=form.cleaned_data['note'],
                investigation_date=form.cleaned_data['investigation_date'],
                result=form.cleaned_data['result'],
                file=form.cleaned_data['file'],
                created_by=request.user,
                updated_by=request.user
            )
            investigation.save()
            messages.success(request, u'เพิ่มรายการสืบสวนโรคสำเร็จ')
            return redirect('supervisors_report_investigation')
    else:
        form = SupervisorsReportInvestigationForm()

    return render(request, 'supervisors/supervisors_report_investigation_form.html', {
        'form': form,
    })


@login_required
# @superuser_required
def supervisors_report_investigation_edit(request, investigation_id):
    investigation = get_object_or_404(ReportInvestigation, id=investigation_id)

    if request.method == 'POST':
        form = SupervisorsReportInvestigationForm(request.POST, request.FILES)
        if form.is_valid():
            investigation.report = form.cleaned_data['report']
            investigation.note = form.cleaned_data['note']
            investigation.investigation_date = form.cleaned_data['investigation_date']
            investigation.result =form.cleaned_data['result']
            if form.cleaned_data['file']:
                investigation.file = form.cleaned_data['file']
            investigation.updated_by = request.user
            investigation.save()

            messages.success(request, u'แก้ไขการสืบสวนโรค #%s สำเร็จ' % investigation.id)
            return redirect('supervisors_report_investigation')
    else:
        form = SupervisorsReportInvestigationForm(initial={
            'report': investigation.report.id,
            'note': investigation.note,
            'investigation_date': investigation.investigation_date,
            'result': 1 if investigation.result else 0,
        })

    return render(request, 'supervisors/supervisors_report_investigation_form.html', {
        'form': form,
        'file': investigation.file,
        'investigation': investigation,
        'edit': True
    })


@login_required
# @superuser_required
def supervisors_report_investigation(request):
    investigation_list = ReportInvestigation.objects.order_by('-investigation_date')
    paginator = Paginator(investigation_list, 100)

    page = request.GET.get('page')
    try:
        investigations = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        investigations = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        investigations = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_report_investigation_list.html', {
        'investigations': investigations
    })


@login_required
# @superuser_required
def supervisors_report_investigation_delete(request, investigation_id):
    investigation = get_object_or_404(ReportInvestigation, id=investigation_id)
    investigation.delete()
    messages.success(request, u'ลบรายการสำเร็จ')
    return redirect('supervisors_report_investigation')


@login_required
# @superuser_required
def supervisors_report_laboratory(request):
    case_list = ReportLaboratoryCase.objects.order_by('-id')
    paginator = Paginator(case_list, 100)

    page = request.GET.get('page')
    try:
        cases = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        cases = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        cases = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_report_lab_case_list.html', {
        'cases': cases
    })


@login_required
# @superuser_required
def supervisors_report_laboratory_create(request):

    if request.method == 'POST':
        data = request.POST.copy()
        data['created_by'] = request.user.id
        data['updated_by'] = request.user.id

        form = SupervisorsReportLaboratoryCaseForm(data)
        if form.is_valid():
            instance = form.save()
            messages.success(request, u'เพิ่มรายการผลแลปสำเร็จ')
            return redirect('supervisors_report_laboratory_edit', instance.id)
    else:
        form = SupervisorsReportLaboratoryCaseForm()

    return render(request, 'supervisors/supervisors_report_lab_case_form.html', {
        'form': form,
    })


@login_required
# @superuser_required
def supervisors_report_laboratory_edit(request, case_id):
    case = get_object_or_404(ReportLaboratoryCase, id=case_id)
    if request.method == 'POST':
        data = request.POST.copy()
        data['created_by'] = request.user.id
        data['updated_by'] = request.user.id

        form = SupervisorsReportLaboratoryCaseForm(data, instance=case)

        if form.is_valid():
            form.save()

            messages.success(request, u'แก้ไขผลแลป #%s สำเร็จ' % case.id)
            return redirect('supervisors_report_laboratory')
    else:
        form = SupervisorsReportLaboratoryCaseForm(instance=case)

    items = case.laboratory_items.order_by('sample_no')
    files = case.laboratory_files.order_by('id')
    causes = AnimalLaboratoryCause.objects.order_by('name')

    import json
    json_cause = json.dumps((AnimalLaboratoryCauseSerializer(causes, many=True).data))

    return render(request, 'supervisors/supervisors_report_lab_case_form.html', {
        'case': case,
        'form': form,
        'items': items,
        'files': files,
        'causes': causes,
        'json_cause': json_cause,
        'edit': True
    })


@login_required
# @superuser_required
def supervisors_report_laboratory_delete(request, case_id):
    case = get_object_or_404(ReportLaboratoryCase, id=case_id)
    case.delete()
    messages.success(request, u'ลบรายการสำเร็จ')
    return redirect('supervisors_report_laboratory')


@login_required
# @superuser_required
def supervisors_report_laboratory_cause(request):
    cause_list = AnimalLaboratoryCause.objects.order_by('name')
    paginator = Paginator(cause_list, 100)

    page = request.GET.get('page')
    try:
        causes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        causes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        causes = paginator.page(paginator.num_pages)

    return render(request, 'supervisors/supervisors_report_lab_cause_list.html', {
        'causes': causes
    })


@login_required
# @superuser_required
def supervisors_report_laboratory_cause_delete(request, cause_id):
    cause = get_object_or_404(AnimalLaboratoryCause, id=cause_id)
    cause.delete()
    messages.success(request, u'ลบรายการสำเร็จ')
    return redirect('supervisors_report_laboratory_cause')

