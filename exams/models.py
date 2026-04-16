from django.db import models
class Subject(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)
    def __str__(self):
        return self.name
class Exam(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(null=True, blank=True)
    def __str__(self):
        return self.name
