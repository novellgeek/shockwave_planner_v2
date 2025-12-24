from django.db import models

from .launch import Launch
from .notam import Notam

class LaunchNotam(models.Model):
    pk = models.CompositePrimaryKey("launch_id", "serial", primary_key=True)

    launch_id = models.ForeignKey(
        Launch,
        on_delete=models.CASCADE
    )

    serial = models.ForeignKey(
        Notam,
        on_delete=models.CASCADE
    )

    models.UniqueConstraint(
        fields=["launch_id", "serial"], 
        name="unique_launch_notam_combo", 
        violation_error_message="A launch can't have the same NOTAM assigned multiple times to it."
        )