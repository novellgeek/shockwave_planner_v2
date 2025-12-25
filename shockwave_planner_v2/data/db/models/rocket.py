from django.db import models

class Rocket(models.Model):
    name = models.TextField(null=False)
    family = models.TextField(null=True)
    variant = models.TextField(null=True)
    manufacturer = models.TextField(null=True)
    country = models.TextField(null=True)
    payload_leo = models.FloatField(null=True)
    payload_gto = models.FloatField(null=True)
    payload_sso = models.FloatField(null=True)
    height = models.FloatField(null=True)
    diameter = models.FloatField(null=True)
    mass = models.FloatField(null=True)
    stages = models.IntegerField(null=True)
    external_id = models.TextField(null=True)