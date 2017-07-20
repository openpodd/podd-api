from django.contrib import admin

# Register your models here.
from areas.models import PlaceCategory, Place


class PlaceCategoryAdmin(admin.ModelAdmin):
    pass

class PlaceAdmin(admin.ModelAdmin):
    pass

admin.site.register(PlaceCategory, PlaceCategoryAdmin)
admin.site.register(Place, PlaceAdmin)