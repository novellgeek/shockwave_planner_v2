from django.db import models

class ReentryVehicle(models.Model):
    name = models.CharField(null=False, unique=True)
    alt_name = models.CharField(null=True)
    family = models.CharField(null=True)
    variant = models.CharField(null=True)
    manufacturer = models.CharField(null=True)
    country = models.CharField(null=True)
    payload = models.IntegerField(null=True)
    decelerator = models.CharField(null=True)
    remarks = models.CharField(null=True)
    external_id = models.CharField(null=True)
