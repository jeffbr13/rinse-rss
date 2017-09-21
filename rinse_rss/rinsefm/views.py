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
            podcasts=PodcastEpisode.objects.all()
        )
    )
