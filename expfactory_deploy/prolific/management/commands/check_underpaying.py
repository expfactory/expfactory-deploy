import datetime
import json

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage, mail_managers
from django.conf import settings

from prolific.outgoing_api import list_active_studies



class Command(BaseCommand):
    help = "Retrieve list of all studies from prolific api. If any active study is underpaying, send email"

    def handle(self, *args, **options):


        try:
            # Prolific api currently not respecting state argument.
            studies = list_active_studies()
            active = [x for x in studies if x['status'] == 'ACTIVE']
            underpaying = [x for x in active if x['is_underpaying'] == True]
            if underpaying:
                funderpaying = json.dumps(underpaying, indent=4, default=str)
                message = EmailMessage(
                    "Underpaying study warning",
                    f"Following studies were found to be underpaying:\n{funderpaying}",
                    settings.SERVER_EMAIL,
                    [a[1] for a in settings.MANAGERS]
                )
                today = datetime.date.today().strftime('%m-%d-%y')
                message.attach(f"underpaying_{today}.json", funderpaying, "application/json")
                message.send()
        except Exception as e:
            mail_managers(
                "Underpaying check failure.",
                f"The api call to list studies failed with the following:\n{e}"
            )
            raise e
        return
