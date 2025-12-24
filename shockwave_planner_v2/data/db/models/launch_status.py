from django.db import models

class LaunchStatus(models.Model):
    def __init__(self):
        name = models.TextField(null=False, unique=True)
        abbr = models.TextField()
        colour = models.TextField()
        description = models.TextField()