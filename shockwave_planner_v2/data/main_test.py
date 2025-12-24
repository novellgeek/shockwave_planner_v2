##############################
# Django specific settings (Please this BEFORE import model class)
##############################
import django
import os
from django.core.management import execute_from_command_line

class LaunchDatabase:
    def __init__(self) -> None:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'db.settings')
        execute_from_command_line(["migrate", "makemigrations"])
        execute_from_command_line(["migrate", "migrate"])

        django.setup()

##############################

if __name__ == "__main__":
    db = LaunchDatabase()

    from db.models.notam import Notam
    
    notam = Notam()
    notam.serial="test"
    notam.save()
