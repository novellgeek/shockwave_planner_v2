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