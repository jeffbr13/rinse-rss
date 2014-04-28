#!python3
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlparse

from lxml.html import fromstring as html
import requests


CONTACT_DETAILS = 'mail@benjeffrey.com (@jeffbr13)'
PODCAST_URL = ''


Enclosure = namedtuple('Enclosure', ['content_length',
                                     'content_type',
                                     'url'])


PodcastItem = namedtuple('PodcastItem', ['title',
                                         'description',
                                         'artist'
                                         'pub_date',
                                         'guid',
                                         'link',
                                         'enclosure'])


Artist = namedtuple('Artist', ['name', 'url', 'description'])


def get_broadcast_artist(element):
    """Find the broadcast artist in the given
    """
    name = [text.strip() for text in element.xpath('.//text()') if text.strip()][0]
    url = element.xpath('./div/h3/a/@href')
    url = url[0] if url else None

    try:
        description = get_artist_description(url)
    except Exception as e:
        description = None
        raise e
    description = get_artist_description(url) if url else None
    return Artist(name, url, description)


def get_artist_description(artist_page_url):
    if not artist_page_url:
        return ''
    artist_page = html(requests.get(artist_page_url).content)
    base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'
    broadcast_time = artist_page.xpath(base_xpath + '/div/h2/text()')[1]
    artist_description = '\n\n'.join(artist_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
    return artist_description


def div_to_podcast_item(element):
    """
    @rtype: PodcastItem
    """
    broadcast_date = datetime.strptime(element.xpath('./@data-air_day')[0], '%Y-%m-%d')
    broadcast_time = datetime.strptime(element.xpath('./@data-airtime')[0], '%H')
    broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())

    artist = get_broadcast_artist(element)

    download_url = element.xpath('./div/div[@class="download icon"]/a/@href')[0]
    download_info = requests.head(download_url).headers

    download_enclosure = Enclosure(url=download_url,
                                   content_length=download_info.get('content-length'),
                                   content_type=download_info.get('content-type'))

    default_show_description = lambda broadcast, artist: '{0} show, broadcast on Rinse FM, from {1}.'.format(artist.name, broadcast.strftime('%A %d %B, %Y at %H:%M'))

    return PodcastItem(title='{0} ({1})'.format(artist.name, broadcast_datetime.strftime('%I%p, %A %d %B %Y').lstrip('0')),
                       description=(artist.description if artist.description
                                    else default_show_description(broadcast_datetime, artist)),
                       artist=artist,
                       pub_date=str(broadcast_datetime),
                       guid=download_url,
                       link=(artist.url if artist.url else download_enclosure.url),
                       enclosure=download_enclosure)


def podcast_items(configuration):
    podcasts_page = html(requests.get(configuration['scrape_url']).content)
    return [div_to_podcast_item(div) for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]')]
