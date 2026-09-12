from django.contrib import admin

from .models import TimetableDay, TimetableEntry, TimetableSlot, TimetableTemplate


class TimetableDayInline(admin.TabularInline):
    model = TimetableDay
    extra = 0


class TimetableSlotInline(admin.TabularInline):
    model = TimetableSlot
    extra = 0


@admin.register(TimetableTemplate)
class TimetableTemplateAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'term', 'name', 'is_published', 'updated_at')
    list_filter = ('is_published', 'term__academic_year', 'term__name')
    search_fields = ('name', 'school_class__class_name')
    inlines = [TimetableDayInline, TimetableSlotInline]


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('timetable', 'day', 'slot', 'class_subject', 'teacher')
    list_filter = ('slot__slot_type',)


admin.site.register(TimetableDay)
admin.site.register(TimetableSlot)
