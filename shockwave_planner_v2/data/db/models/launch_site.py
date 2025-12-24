from django.db import models

class LaunchSite(models.Model):
    name = models.TextField(null=False)
    launch_pad = models.TextField(null=False)
    longitude = models.FloatField()
    latitude = models.FloatField()
    country = models.TextField()
    site_type = models.TextField(default="LAUNCH")
    external_id = models.TextField()
    turnaround_days = models.IntegerField(default=7)

    models.UniqueConstraint(
        fields=["location","launch_pad"], 
        name="unique_location_launchpad_combo",
        violation_error_message="A Launch site can't have duplicate launch pads"
        )
