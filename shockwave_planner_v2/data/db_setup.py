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
    from data.db.models.launch_status import LaunchStatus
    LaunchStatus.objects.bulk_create(
        [
            LaunchStatus(
                name='Scheduled', 
                abbr='SCH', 
                colour='#FFFF00', 
                description='Launch is scheduled'),
            LaunchStatus(
                name='Go for Launch', 
                abbr='GO', 
                colour='#00FF00', 
                description='Cleared for launch'),
            LaunchStatus(
                name='Success', 
                abbr='SUC', 
                colour='#00AA00', 
                description='Launch successful'),
            LaunchStatus(
                name='Failure', 
                abbr='FAIL', 
                colour='#FF0000', 
                description='Launch failed'),
            LaunchStatus(
                name='Partial Failure', 
                abbr='PF', 
                colour='#FFA500', 
                description='Partial failure'),
            LaunchStatus(
                name='Scrubbed', 
                abbr='SCR', 
                colour='#808080', 
                description='Launch scrubbed'),
            LaunchStatus(
                name='Hold', 
                abbr='HOLD', 
                colour='#FFAA00', 
                description='Launch on hold'),
            LaunchStatus(
                name='In Flight', 
                abbr='FLT', 
                colour='#00AAFF', 
                description='Vehicle in flight'),
        ],
        ignore_conflicts=True
    )