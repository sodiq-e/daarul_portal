from django.contrib import admin
from .models import Score
@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('student','exam','subject','score','_grade')
    list_filter = ('exam','subject')
    def _grade(self,obj):
        return obj.grade()
    _grade.short_description = 'Grade'
