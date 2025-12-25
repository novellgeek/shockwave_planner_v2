from django.db import models

# Other model imports
from .notam import Notam
from .rocket import Rocket
from .launch_site import LaunchSite
from .launch_status import LaunchStatus

class Launch(models.Model):
    launch_date = models.DateField()
    launch_time = models.TimeField(null = True)
    launch_window_start = models.DateTimeField(null = True)
    launch_window_end = models.DateTimeField(null = True)
    mission_name = models.TextField(null = True)
    payload_name = models.TextField(null = True)
    payload_mass = models.FloatField(null = True)
    orbit_type = models.TextField(null = True)
    orbit_altitude = models.FloatField(null = True)
    inclination = models.FloatField(null = True)
    success = models.BooleanField(null = True)
    failure_reason = models.TextField(null = True)
    remarks = models.TextField(null = True)
    source_url = models.TextField(null = True)
    last_updated = models.DateTimeField(null = True)
    notam_reference = models.TextField(null = True)
    data_source = models.TextField(null = True, default="MANUAL")
    external_id = models.TextField(null = True)
    last_synced = models.DateTimeField(null = True, auto_now_add=True)

    site = models.ForeignKey(LaunchSite, on_delete=models.CASCADE)
    rocket = models.ForeignKey(Rocket, on_delete=models.CASCADE)
    status = models.ForeignKey(LaunchStatus, on_delete=models.CASCADE)
    notams = models.ManyToManyField(Notam, through="LaunchNotam")

    @property
    def launch_datetime(self):
        return 