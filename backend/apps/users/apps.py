from django.apps import AppConfig

_PRAGMA_BOUND = False


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"

    def ready(self):
        global _PRAGMA_BOUND
        if _PRAGMA_BOUND:
            return
        from django.db.backends.signals import connection_created

        def _sqlite_pragma(sender, connection, **kwargs):
            if connection.vendor == "sqlite":
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")

        connection_created.connect(_sqlite_pragma)
        _PRAGMA_BOUND = True
