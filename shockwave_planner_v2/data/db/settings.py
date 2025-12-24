import os

BASE_DIR = os.path.dirname(os.getcwd()+"\\shockwave_planner_v2\\")

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test.db"),
        "OPTIONS": {
            "init_command": "PRAGMA foreign_keys = ON;"
        },
    }
}

INSTALLED_APPS = ("db",)