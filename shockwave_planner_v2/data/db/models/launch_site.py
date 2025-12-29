from django.db import models

class LaunchSite(models.Model):
    name = models.TextField(null=False)
    launch_pad = models.TextField(null=False)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.TextField(null=True)
    site_type = models.TextField(null=True, default="LAUNCH")
    external_id = models.TextField(null=True)
    turnaround_days = models.IntegerField(default=7)

    class Meta:
        constraints = [
            models.UniqueConstraint(
            fields=["name","launch_pad"], 
            name="unique_location_launchpad_combo",
            violation_error_message="A Launch site can't have duplicate launch pads"
            )
        ]
