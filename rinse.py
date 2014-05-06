#!python3
import logging
from collections import namedtuple
from datetime import datetime

import requests
from lxml.html import fromstring as html


CONTACT_DETAILS = 'mail@benjeffrey.com (@jeffbr13)'
PODCAST_URL = ''


Enclosure = namedtuple('Enclosure', ['content_length',
                                     'content_type',
                                     'url'])


PodcastItem = namedtuple('PodcastItem', ['title',
                                         'description',
                                         'artist',
                                         'pub_date',
                                         'guid',
                                         'url',
                                         'enclosure'])


Artist = namedtuple('Artist', ['name',
                               'url_safe_name',
                               'description',
                               'url'])


def artist(element):
    """
    @rtype: Artist
    """
    logging.debug('Initialising broadcast artist information from element')
    name = [text.strip() for text in element.xpath('.//text()') if text.strip()][0]
    url = element.xpath('./div/h3/a/@href')
    if url:
        url = url[0]
        logging.debug(url)
        url_safe_name = url.rsplit('/', 2)[-2]
        logging.debug(url_safe_name)
    else:
        url = None
        url_safe_name = None
    description = fetch_artist_description(url)
    logging.debug('Successfully initialised <Artist: {0}>'.format(name))
    return Artist(name, url_safe_name, description, url)


def fetch_artist_description(artist_page_url):
    logging.debug('Fetching artist description from "{0}"'.format(artist_page_url))
    if not artist_page_url:
        return ''
    artist_page = html(requests.get(artist_page_url).content)
    base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'
    broadcast_time = artist_page.xpath(base_xpath + '/div/h2/text()[1]')
    artist_description = '\n\n'.join(artist_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
    logging.debug('Successfully extracted artist description from {0}'.format(artist_page_url))
    return artist_description


def podcast_item(element):
    """
    @rtype: PodcastItem
    """
    logging.info('Initialising PodcastItem from element')
    broadcast_date = datetime.strptime(element.xpath('./@data-air_day')[0], '%Y-%m-%d')
    broadcast_time = datetime.strptime(element.xpath('./@data-airtime')[0], '%H')
    broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())

    broadcast_artist = artist(element)

    download_url = element.xpath('./div/div[@class="download icon"]/a/@href')[0]
    download_headers = requests.head(download_url).headers

    download_enclosure = Enclosure(url=download_url,
                                   content_length=download_headers.get('content-length'),
                                   content_type=download_headers.get('content-type'))

    podcast_item_title = '{0} ({1})'.format(broadcast_artist.name, broadcast_datetime.strftime('%I%p, %A %d %B %Y').lstrip('0'))

    if broadcast_artist.description:
        podcast_item_description = broadcast_artist.description
    else:
        podcast_item_description = 'The {0} show, broadcast on Rinse FM, on {1}.'.format(broadcast_artist.name, broadcast_datetime.strftime('%A %d %B, %Y at %H:%M'))

    logging.info('Successfully got <PodcastItem: {0}> data from element'.format(podcast_item_title))
    return PodcastItem(title=podcast_item_title,
                       description=podcast_item_description,
                       artist=broadcast_artist,
                       pub_date=broadcast_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000'),
                       guid=download_url,
                       url=(broadcast_artist.url if broadcast_artist.url else download_enclosure.url),
                       enclosure=download_enclosure)


def podcast_items(configuration):
    logging.info("Fetching podcast items from {0}".format(configuration['scrape_url']))
    podcasts_page = html(requests.get(configuration['scrape_url']).content)
    #TODO: scrape more than the front page
    return [podcast_item(div) for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]')]
