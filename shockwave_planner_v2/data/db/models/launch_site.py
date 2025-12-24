from django.db import models

class LaunchSite(models.Model):
    def __init__(self):
        location = models.TextField(null=False)
        launch_pad = models.TextField(null=False)
        longitude = models.FloatField()
        latitude = models.FloatField()
        country = models.TextField()
        site_type = models.TextField(default="LAUNCH")
        external_id = models.TextField()
        turnaround_days = models.IntegerField(default=7)

        models.UniqueConstraint(fields=["location","launch_pad"])
