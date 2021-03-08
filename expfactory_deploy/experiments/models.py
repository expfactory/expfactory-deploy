# from model_utils.fields import StatusField
import reversion
from django.db import models
from model_utils import Choices
from model_utils.models import StatusModel


@reversion.register()
class ExperimentRepo(models.Model):
    """ Location of a repository that contains an experiment """

    origin = models.URLField()


@reversion.register()
class ExperimentInstance(models.Model):
    """ A specific point in time of an experiment. """

    pass


@reversion.register()
class Battery(models.Model):
    """ collection of experiments """

    pass


@reversion.register()
class BatteryDeployment(StatusModel):
    """ Specific deployment of a battery  """

    STATUS = Choices("draft", "published")


@reversion.register()
class ExperimentFramework(models.Model):
    """ Framework used by experiments. """

    pass
