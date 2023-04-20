from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "users"
    verbose_name = _("Users")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        try:
            import expfactory_deploy.users.signals  # noqa F401
        except ImportError:
            pass
