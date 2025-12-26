from django.db import models

class ReentrySite(models.Model):
    name = models.TextField(null=False)
    drop_zone = models.TextField(null=False)
    latitude = models.FloatField()
    longitude = models.FloatField()
    country = models.TextField()
    zone_type = models.TextField()
    external_id = models.TextField(unique=True)
    turnaround_days = models.IntegerField(default=7)

    models.UniqueConstraint(
        fields=["name","drop_zone"], 
        name="unique_location_dropzone_combo",
        violation_error_message="A Reentry site can't have duplicate drop zones"
        )


