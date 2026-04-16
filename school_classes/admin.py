from django.contrib import admin
from .models import SchoolClasses

class SchoolClassesAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'level', 'description')
    search_fields = ('class_name', 'level')

admin.site.register(SchoolClasses, SchoolClassesAdmin)
