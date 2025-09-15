from django.db.models import TextField
from django.db.models.functions import Length

import experiments.models as em

TextField.register_lookup(Length)

def export_pids():
    pids = set(em.Subject.objects.filter(prolific_id__length=24).values_list('prolific_id', flat=True))

    exclude = ["6410d74c29d97f193806ca65", "66df7183ca005faefb450369"]
    pids = [x for x in pids if x not in exclude]

    with open('participant_ids.txt', 'w') as fp:
        fp.writelines('\n'.join(pids))
