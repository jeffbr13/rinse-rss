from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.syndication.views import Feed
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.feedgenerator import Rss201rev2Feed

from .models import PodcastEpisode


def index(request: HttpRequest):
    return render(request, 'index.html')


class PodcastFeed(Rss201rev2Feed):
    def root_attributes(self):
        attrs = super().root_attributes()
        attrs['xmlns:itunes'] = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        return attrs

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        handler.addQuickElement('itunes:image', attrs={'href': self.feed.get('artwork_url', '')})
        handler.addQuickElement('itunes:subtitle', self.feed.get('subtitle', ''))
        handler.addQuickElement('itunes:summary', self.feed.get('description', ''))
        handler.addQuickElement('itunes:category', attrs={'text': self.feed.get('category', '')})
        handler.addQuickElement('itunes:keywords', ', '.join(self.feed.get('categories', [])))
        handler.addQuickElement('itunes:explicit', 'yes' if self.feed.get('explicit') else 'clean')

        handler.addQuickElement('itunes:author', self.feed.get('author_name'))
        handler.startElement('itunes:owner', {})
        handler.addQuickElement('itunes:name', self.feed.get('owner_name'))
        handler.addQuickElement('itunes:email', self.feed.get('owner_email'))
        handler.endElement('itunes:owner')

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        handler.addQuickElement('itunes:summary', item.get('description'))
        handler.addQuickElement('itunes:duration', item.get('duration'))
        handler.addQuickElement('itunes:author', item.get('author_name'))


class AllPodcastsFeed(Feed):
    feed_type = PodcastFeed
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
    category = 'Music'
    categories = ('Rinse FM', 'rinse', 'grime', 'garage', 'dubstep', 'house', 'deep house', 'techno', 'urban', 'music')
    explicit = True
    author_name = 'Rinse RSS'
    copyright = 'Rinse RSS'

    def feed_extra_kwargs(self, obj):
        return {
            'category': self.category,
            'explicit': True,
            'artwork_url': static('artwork.png'),
            'owner_name': 'Ben Jeffrey',
            'owner_email': 'br-rss@jeffbr13.net',
        }

    def items(self):
        return PodcastEpisode.objects.all()

    def item_link(self, item):
        return 'http://podcast.dgen.net/rinsefm/podcast/%s' % item.slug

    def item_guid(self, item):
        return item.audio_url

    def item_title(self, item):
        return item.title

    def item_enclosure_url(self, item):
        return item.audio_url

    def item_enclosure_length(self, item):
        return item.audio_content_length

    def item_enclosure_mime_type(self, item):
        return item.audio_content_type

    def item_pubdate(self, item):
        return item.broadcast_date
