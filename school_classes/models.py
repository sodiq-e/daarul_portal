from django.db import models

class SchoolClasses(models.Model):
    class_name = models.CharField(max_length=50, unique=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.class_name
