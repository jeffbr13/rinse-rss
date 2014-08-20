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


Podcast = namedtuple('Podcast', ['title',
                                 'description',
                                 'show',
                                 'pub_date',
                                 'guid',
                                 'url',
                                 'enclosure'])


Show = namedtuple('Show', ['name',
                           'url_safe_name',
                           'description',
                           'url'])


def show(element):
    """
    Scrape show information about a div.podcast-list-item element.

    :type element: lxml.html.HtmlElement
    :rtype: Show
    """
    logging.debug('Initialising broadcast show information from element')
    url = element.xpath('./div/h3/a/@href')
    if url:
        url = url[0]
        logging.debug(url)
        url_safe_name = url.rsplit('/', 2)[-2]
        logging.debug(url_safe_name)
    else:
        url = None
        url_safe_name = None
    name, description = show_details(url)
    if not name:
        name = [text.strip() for text in element.xpath('.//text()') if text.strip()][0]

    logging.debug('Successfully initialised <Show: {0}>'.format(name))
    return Show(name, url_safe_name, description, url)


def show_details(show_page_url):
    """
    Attempts to scrape the Rinse FM show page for information.

    :type show_page_url: str
    :rtype: (str, str)
    :returns: The show's name and a description, if one exists. An empty string, otherwise.
    """
    logging.debug('Fetching show description from "{0}"'.format(show_page_url))
    if not show_page_url:
        return (None, None)

    show_page = html(requests.get(show_page_url).content)
    base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'

    try:
        show_name = show_page.xpath(base_xpath + '/div/h2/text()')[0]
        logging.debug('Successfully extracted show name ({0}) from {1}'.format(show_name, show_page_url))
    except IndexError:
        show_name = None

    presenter_description = '\n\n'.join(show_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
    logging.debug('Successfully extracted show description from {0}'.format(show_page_url))
    return (show_name, presenter_description)


def podcast(element):
    """
    Build a Podcast using the information in a div.podcast-list-item from the podcasts page.

    :type element: lxml.html.HtmlElement
    :rtype: Podcast
    """
    logging.info('Initialising Podcast from element')
    broadcast_date = datetime.strptime(element.xpath('./@data-air_day')[0], '%Y-%m-%d')
    broadcast_time = datetime.strptime(element.xpath('./@data-airtime')[0], '%H')
    broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())

    broadcast_show = show(element)

    # Get accurate download information for the RSS Enclosure
    download_url = element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()
    download_headers = requests.head(download_url).headers

    download_enclosure = Enclosure(url=download_url,
                                   content_length=download_headers.get('content-length'),
                                   content_type=download_headers.get('content-type'))

    show_description = broadcast_show.description if broadcast_show.description else ''

    logging.info('Successfully got <Podcast: {0}> data from element'.format(broadcast_show.name))
    return Podcast(title=broadcast_show.name,
                   description=show_description,
                   show=broadcast_show,
                   pub_date=broadcast_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000'),
                   guid=download_url,
                   url=(broadcast_show.url if broadcast_show.url else download_enclosure.url),
                   enclosure=download_enclosure)


def podcasts(scrape_url):
    """
    :param scrape_url: Webpage URL to scrape for Podcasts
    :return: An iterable of scraped Podcasts

    :rtype: PodcastShow
    """
    logging.info("Fetching podcast items from {0}".format(scrape_url))
    podcasts_page = html(requests.get(scrape_url).content)
    #TODO: scrape more than the front page
    return [podcast(div) for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]')]
