from django.contrib import admin
from .models import TraitCategory, Trait, StudentTraitRating
admin.site.register(TraitCategory)
admin.site.register(Trait)
admin.site.register(StudentTraitRating)
