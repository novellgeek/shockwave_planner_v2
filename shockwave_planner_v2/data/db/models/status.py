from django.db import models

class Status(models.Model):
    name = models.TextField(null=False, unique=True)
    abbr = models.TextField()
    colour = models.TextField()
    description = models.TextField()