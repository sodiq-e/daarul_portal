from django.db import models
from students.models import Student
from exams.models import Exam, Subject
from school_classes.models import SchoolClasses

class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    class Meta:
        unique_together = ('student','exam','subject')
    def grade(self):
        s = float(self.score)
        if s >= 70: return 'A'
        if s >= 60: return 'B'
        if s >= 50: return 'C'
        if s >= 45: return 'D'
        if s >= 40: return 'E'
        return 'F'
    def remark(self):
        return {'A':'Excellent','B':'Very Good','C':'Good','D':'Fair','E':'Pass','F':'Fail'}[self.grade()]

class Promotion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    from_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE, related_name='promotions_from')
    to_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE, related_name='promotions_to')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    promoted_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} promoted from {self.from_class} to {self.to_class}"
