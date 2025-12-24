from django.db import models

class Notam(models.Model):
    serial = models.CharField(primary_key=True)

    # TODO add further attributes to facilitate future features (e.g. mapping)