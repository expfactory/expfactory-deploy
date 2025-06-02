from prolific import models as pm

failed_to_warn = []
failed_to_flag = []
def fail_to_warn():
    scolls = pm.StudyCollection.objects.filter(active=True, name__contains='[main]')
    for sc in scolls:
        warn_delta = sc.inter_study_delay + sc.study_time_to_warning
        flag_delta = warn_delta + sc.study_grace_interval
        scses = pm.StudyCollectionSubject.objects.filter(study_collection=sc)
        for scs in scses:
            sses = pm.StudySubject.objects.filter(subject=scs.subject, study__study_collection=scs.study_collection).order_by('study__rank')
            assgns = [x.assignment for x in sses]
            for i in range(len(assgns) - 1):
                delta = assgns[i+1].status_changed - assgns[i].status_changed 
                if (delta > flag_delta):
                    failed_to_flag.append((delta, assgns[i+1]))
                elif (delta > warn_delta):
                    failed_to_warn.append((delta, assgns[i+1]))
    return failed_to_warn, failed_to_flag
