from django.db import models

# Other model imports
from .notam import Notam
from .rocket import Rocket
from .launch_site import LaunchSite
from .launch_status import LaunchStatus

class Launch(models.Model):
    launch_date = models.DateField(null = False)
    launch_time = models.TimeField()
    launch_window_start = models.DateTimeField()
    launch_window_end = models.DateTimeField()
    mission_name = models.TextField()
    payload_name = models.TextField()
    payload_mass = models.FloatField()
    orbit_type = models.TextField()
    orbit_altitude = models.FloatField()
    inclination = models.FloatField()
    success = models.BooleanField()
    failure_reason = models.TextField()
    remarks = models.TextField()
    source_url = models.TextField()
    last_updated = models.DateTimeField(auto_now_add=True)
    notam_reference = models.TextField()
    data_source = models.TextField(default="MANUAL")
    external_id = models.TextField()
    last_synced = models.DateTimeField()

    site = models.ForeignKey(LaunchSite, on_delete=models.CASCADE)
    rocket = models.ForeignKey(Rocket, on_delete=models.CASCADE)
    status = models.ForeignKey(LaunchStatus, on_delete=models.CASCADE)
    notams = models.ManyToManyField(Notam, through="LaunchNotam")