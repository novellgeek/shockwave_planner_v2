from django.db import models

# Other model imports
from .launch import Launch
from .reentry_site import ReentrySite
from .status import Status

class Reentry(models.Model):
    reentry_date = models.DateField()
    reentry_time = models.TimeField(null = True)
    vehicle_component = models.TextField(null = True)
    reentry_type = models.TextField(null = True)
    remarks = models.TextField(null = True)
    data_source = models.TextField(null = True, default="MANUAL")
    external_id = models.TextField(null = True)
    
    launch = models.ForeignKey(Launch, on_delete=models.CASCADE)
    site = models.ForeignKey(ReentrySite, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)