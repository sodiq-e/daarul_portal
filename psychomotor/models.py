from django.db import models
from students.models import Student
from settingsapp.models import TenantModel

class TraitCategory(TenantModel):
    name = models.CharField(max_length=120)
    def __str__(self): return self.name
class Trait(TenantModel):
    category = models.ForeignKey(TraitCategory, on_delete=models.CASCADE, related_name='traits')
    name = models.CharField(max_length=120)
    def __str__(self): return self.name
class StudentTraitRating(TenantModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    trait = models.ForeignKey(Trait, on_delete=models.CASCADE)
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE)
    rating = models.IntegerField(default=3)
    remark = models.CharField(max_length=255, blank=True)
    class Meta:
        unique_together = ('student','trait','exam')
