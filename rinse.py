#!python3
import logging
from collections import namedtuple
from datetime import datetime

import requests
from lxml.html import fromstring as html


CONTACT_DETAILS = 'mail@benjeffrey.net (@jeffbr13)'
PODCAST_URL = ''

Enclosure = namedtuple('Enclosure', ['content_length',
                                     'content_type',
                                     'url'])


PodcastShow = namedtuple('PodcastShow', ['title',
                                         'description',
                                         'presenter',
                                         'pub_date',
                                         'guid',
                                         'url',
                                         'enclosure'])


Presenter = namedtuple('Presenter', ['name',
                                     'url_safe_name',
                                     'description',
                                     'url'])


def presenter(element):
    """
    @rtype: Presenter
    """
    logging.debug('Initialising broadcast presenter information from element')
    url = element.xpath('./div/h3/a/@href')
    if url:
        url = url[0]
        logging.debug(url)
        url_safe_name = url.rsplit('/', 2)[-2]
        logging.debug(url_safe_name)
    else:
        url = None
        url_safe_name = None
    name, description = presenter_details(url)
    if not name:
        name = [text.strip() for text in element.xpath('.//text()') if text.strip()][0]

    logging.debug('Successfully initialised <Presenter: {0}>'.format(name))
    return Presenter(name, url_safe_name, description, url)


def presenter_details(presenter_page_url):
    """
    Fetches the Rinse FM presenter page, and scrapes their:

    - name
    - description

    @rtype: (string, string)
    """
    logging.debug('Fetching presenter description from "{0}"'.format(presenter_page_url))
    if not presenter_page_url:
        return (None, None)

    presenter_page = html(requests.get(presenter_page_url).content)
    base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'

    try:
        presenter_name = presenter_page.xpath(base_xpath + '/div/h2/text()')[0]
        logging.debug('Successfully extracted presenter name ({0}) from {1}'.format(presenter_name, presenter_page_url))
    except IndexError:
        presenter_name = None

    presenter_description = '\n\n'.join(presenter_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
    logging.debug('Successfully extracted presenter description from {0}'.format(presenter_page_url))
    return (presenter_name, presenter_description)


def show(element):
    """
    @rtype: PodcastShow
    """
    logging.info('Initialising PodcastShow from element')
    broadcast_date = datetime.strptime(element.xpath('./@data-air_day')[0], '%Y-%m-%d')
    broadcast_time = datetime.strptime(element.xpath('./@data-airtime')[0], '%H')
    broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())

    broadcast_presenter = presenter(element)

    download_url = element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()
    download_headers = requests.head(download_url).headers

    download_enclosure = Enclosure(url=download_url,
                                   content_length=download_headers.get('content-length'),
                                   content_type=download_headers.get('content-type'))

    show_title = '{0} ({1})'.format(broadcast_presenter.name, broadcast_datetime.strftime('%I%p, %A %d %B %Y').lstrip('0'))

    if broadcast_presenter.description:
        show_description = broadcast_presenter.description
    else:
        show_description = 'The {0} show, broadcast on Rinse FM, on {1}.'.format(broadcast_presenter.name, broadcast_datetime.strftime('%A %d %B, %Y at %H:%M'))

    logging.info('Successfully got <PodcastShow: {0}> data from element'.format(show_title))
    return PodcastShow(title=show_title,
                       description=show_description,
                       presenter=broadcast_presenter,
                       pub_date=broadcast_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000'),
                       guid=download_url,
                       url=(broadcast_presenter.url if broadcast_presenter.url else download_enclosure.url),
                       enclosure=download_enclosure)


def shows(configuration):
    logging.info("Fetching podcast items from {0}".format(configuration['scrape_url']))
    podcasts_page = html(requests.get(configuration['scrape_url']).content)
    #TODO: scrape more than the front page
    return [show(div) for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]')]
