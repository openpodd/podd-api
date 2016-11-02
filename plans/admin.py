from django.contrib import admin
from plans.models import Plan, PlanLevel


class PlanAdmin(admin.ModelAdmin):
    pass

class PlanLevelAdmin(admin.ModelAdmin):
    pass

admin.site.register(Plan, PlanAdmin)
admin.site.register(PlanLevel, PlanLevelAdmin)
