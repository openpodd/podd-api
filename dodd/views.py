from django.shortcuts import render
from django.http import HttpResponse


from dodd.tasks import create_podd_report_from_public_report
# Create your views here.
def test_link_report(request):
    create_podd_report_from_public_report(184936)
    return HttpResponse("ok")