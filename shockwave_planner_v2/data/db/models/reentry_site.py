from django.db import models

class ReentrySite(models.Model):
    name = models.TextField(null=False)
    drop_zone = models.TextField(null=False)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.TextField(null=True)
    zone_type = models.TextField(null=True)
    external_id = models.TextField(null=True)
    turnaround_days = models.IntegerField(default=7)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name","drop_zone"], 
                name="unique_location_dropzone_combo",
                violation_error_message="A Reentry site can't have duplicate drop zones"
            )
        ]

