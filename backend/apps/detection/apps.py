from django.apps import AppConfig


class DetectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.detection"
    label = "detection"

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError

        try:
            from .services import fail_stale_batches

            fail_stale_batches()
        except (OperationalError, ProgrammingError):
            pass
