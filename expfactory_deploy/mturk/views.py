from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from mturk import forms as forms
import boto_utils

def battery_id_from_url(url):
    pattern = '/serve/(\d+)/'
    match = re.search(pattern, url)
    if match is None:
        return None
    try:
        return match.group(1)
    except IndexError:
        return None

'''
class CreateHit(LoginRequiredMixin, FormView):
    template_name = 'mturk/create_hit.html'
    form_class = forms.MturkHit
    success_url = reverse_lazy('mturk:list_hits')
    def form_valid(self, form):
        # self.kwargs['level']

        return super().form_valid(form)
'''


@login_required
def hits_list(request):
    client = boto_utils.BotoWrapper()
    hits = client.get_all_hits()
    battery_urls = {}
    for key in hits.keys():
        bid = battery_id_from_url(key)
        detail_url = reverse("experiments:battery-detail", args=[bid])
        battery_urls[key] = detail_url

    context =  {hits_by_url: hits, battery_urls: battery_urls}
    return render(request, "mturk/list_hits.html", context)

@login_required
def summaries_list(request):
    client = boto_utils.BotoWrapper()
    hits = client.get_all_hits()
    summaries = {}
    battery_urls = {}
    for key in hits.keys():
        pending = 0
        available = 0
        complete = 0
        bid = battery_id_from_url(key)
        detail_url = reverse("experiments:battery-detail", args=[bid])
        battery_urls[key] = detail_url

    context =  {hits_by_url: hits, battery_urls: battery_urls}
    return render(request, "mturk/list_hits.html", context)



@login_required(request):
def assignments_list(request, url):
    client = boto_utils.BotoWrapper()
    client.list_assignments(url)

