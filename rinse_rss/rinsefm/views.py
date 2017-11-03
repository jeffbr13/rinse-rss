from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpRequest
from django.shortcuts import render
from podcast_feed import PodcastFeed

from .models import PodcastEpisode


def index(request: HttpRequest):
    return render(request, 'index.html', context={'episodes': PodcastEpisode.objects.all()[:10]})


class AllPodcastsFeed(PodcastFeed):
    link = 'http://rinse.fm/'
    title = 'Rinse FM'
    subtitle = "London's favourite pirate radio station"
    description = (
        "London's favorite pirate radio station now available in unofficial podcast format.\n\n"
        "Rinse FM is uniquely placed at the hub of the Capitalʼs thriving British underground music community, "
        "demonstrating throughout 18 years of broadcasting that they provide a vital, unique and exceptionally "
        "successful, grass-roots gateway into broadcast radio and the wider music industry.\n\n"
        "Rinseʼs DJs and MCs have won Mercury Music Prize awards, with nominations for numerous others,"
        "gold discs in recognition of sales, and widespread critical acclaim. "
        "In stark contrast to the homogenized radio landscape Rinse FM seeks to champion "
        "the diverse needs of young London and those passionate about youth-orientated music culture, "
        "currently showcasing genres typically referred to as Dubstep, UK Funky and Grime "
        "while interacting with and influencing those scenes. "
        "Rinseʼs fiercely grass-roots broadcasting ethos engages massively under-represented communities, "
        "especially 15-24 year olds"
    )
    categories = ('Rinse FM', 'rinse', 'grime', 'garage', 'dubstep', 'house', 'deep house', 'techno', 'urban', 'music')
    # iTunes podcast attributes
    artwork_link = static('artwork.png')
    itunes_category = 'Music'
    explicit = True
    author_name = 'Rinse RSS'
    copyright = 'Rinse RSS'
    owner_name = 'Ben Jeffrey'
    owner_email = 'br-rss@jeffbr13.net'

    def items(self):
        return PodcastEpisode.objects.all()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return ''

    def item_enclosure_url(self, item):
        return item.audio_url

    def item_enclosure_length(self, item):
        return item.audio_content_length

    def item_enclosure_mime_type(self, item):
        return item.audio_content_type

    def item_pubdate(self, item):
        return item.broadcast_date
