import django
import os
from django.core.management import execute_from_command_line
import sys

# TODO add documentation
def init_db():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data.db_settings')
    execute_from_command_line(["migrate", "makemigrations"])
    execute_from_command_line(["migrate", "migrate"])

    django.setup()

    # Preload Launch Status
    from data.db.models.status import Status
    Status.objects.bulk_create(
        [
            Status(
                name='Scheduled', 
                abbr='SCH', 
                colour='#FFFF00', 
                description='Launch is scheduled'),
            Status(
                name='Go for Launch', 
                abbr='GO', 
                colour='#00FF00', 
                description='Cleared for launch'),
            Status(
                name='Success', 
                abbr='SUC', 
                colour='#00AA00', 
                description='Launch successful'),
            Status(
                name='Failure', 
                abbr='FAIL', 
                colour='#FF0000', 
                description='Launch failed'),
            Status(
                name='Partial Failure', 
                abbr='PF', 
                colour='#FFA500', 
                description='Partial failure'),
            Status(
                name='Scrubbed', 
                abbr='SCR', 
                colour='#808080', 
                description='Launch scrubbed'),
            Status(
                name='Hold', 
                abbr='HOLD', 
                colour='#FFAA00', 
                description='Launch on hold'),
            Status(
                name='In Flight', 
                abbr='FLT', 
                colour='#00AAFF', 
                description='Vehicle in flight'),
        ],
        ignore_conflicts=True
    )