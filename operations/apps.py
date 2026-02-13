from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operations'
    verbose_name = 'Λειτουργίες & Κόστη'
    
    def ready(self):
        """
        Import signals when the app is ready
        This ensures signals are registered and active
        """
        import operations.signals
