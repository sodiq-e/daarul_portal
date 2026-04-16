from django.db import models
from students.models import Student
class TraitCategory(models.Model):
    name = models.CharField(max_length=120)
    def __str__(self): return self.name
class Trait(models.Model):
    category = models.ForeignKey(TraitCategory, on_delete=models.CASCADE, related_name='traits')
    name = models.CharField(max_length=120)
    def __str__(self): return self.name
class StudentTraitRating(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    trait = models.ForeignKey(Trait, on_delete=models.CASCADE)
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE)
    rating = models.IntegerField(default=3)
    remark = models.CharField(max_length=255, blank=True)
    class Meta:
        unique_together = ('student','trait','exam')
