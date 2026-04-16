from django.db import models
from students.models import Student
class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=True)
    def __str__(self): return f"{self.student} - {self.date} - {'P' if self.present else 'A'}"
