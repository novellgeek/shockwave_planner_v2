from django.db import models

class SyncLog(models.Model):
    sync_time = models.DateTimeField(auto_now_add=True)
    data_source = models.CharField(null=True)
    records_added = models.BigIntegerField(null=True)
    records_updated = models.BigIntegerField(null=True)
    status = models.CharField(null=True)
    error_msg = models.CharField(null=True)