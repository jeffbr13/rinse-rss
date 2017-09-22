from django.http import HttpRequest
from django.shortcuts import render

from .models import PodcastEpisode


def index(request: HttpRequest):
    return render(request, 'index.html')


def podcast_feed(request: HttpRequest):
    return render(
        request,
        'rss.xml',
        context=dict(
            scheme=request._get_scheme(),
            hostname=request.get_host(),
            podcasts=PodcastEpisode.objects.all(),
        )
    )
