from django.db import models

class Rocket(models.Model):
    def __init__(self):
        name = models.TextField()
        family = models.TextField()
        variant = models.TextField()
        manufacturer = models.TextField()
        country = models.TextField()
        payload_leo = models.FloatField()
        paload_gto = models.FloatField()
        height = models.FloatField()
        diameter = models.FloatField()
        mass = models.FloatField()
        stages = models.IntegerField()
        external_id = models.TextField()