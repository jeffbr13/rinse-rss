#!python3
import logging
from collections import namedtuple
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy

import requests
from lxml.html import fromstring as html


db = SQLAlchemy()


class IndividualPodcast(db.Model):
    guid = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    broadcast_date = db.Column(db.DateTime)
    web_url = db.Column(db.String(200))

    enclosure_url = db.Column(db.String(200))
    enclosure_content_length = db.Column(db.Integer)
    enclosure_content_type = db.Column(db.String(100))

    show_slug = db.Column(db.String(200), db.ForeignKey("recurring_show.slug"))

    def __init__(self, title, description, broadcast_date, web_url,
                 enclosure_url, enclosure_content_length, enclosure_content_type,
                 show):
        self.title = title
        self.description = description
        self.broadcast_date = broadcast_date
        self.web_url = web_url
        self.enclosure_url = enclosure_url
        self.enclosure_content_length = enclosure_content_length
        self.enclosure_content_type = enclosure_content_type
        self.show_slug = show.slug
        self.guid = self.enclosure_url

    def __repr__(self):
        return "<IndividualPodcast: %s>" % self.guid


class RecurringShow(db.Model):
    slug = db.Column(db.String(200), primary_key=True)

    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    web_url = db.Column(db.String(200))

    podcasts = db.relationship("IndividualPodcast", backref=db.backref("show"))

    def __init__(self, slug, name, description, web_url):
        self.slug = slug
        self.name = name
        self.description = description
        self.web_url = web_url

    def __repr__(self):
        return "<RecurringShow: %s>" % self.slug


def show(html_element):
    """
    Scrape show information about a div.podcast-list-item element.

    :type html_element: lxml.html.HtmlElement
    :rtype: RecurringShow
    """
    logging.debug('Initialising broadcast show information from HTML element')
    url = html_element.xpath('./div/h3/a/@href')
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
        name = [text.strip() for text in html_element.xpath('.//text()') if text.strip()][0]

    logging.debug('Successfully initialised <Show: {0}>'.format(name))
    return RecurringShow(name=name, slug=url_safe_name, description=description, web_url=url)


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
    return show_name, presenter_description


def podcast(html_element):
    """
    Build a Podcast using the information in a div.podcast-list-item from the podcasts page.

    :type html_element: lxml.html.HtmlElement
    :rtype: IndividualPodcast
    """
    logging.info('Initialising Podcast from HTML element')
    broadcast_date = datetime.strptime(html_element.xpath('./@data-air_day')[0], '%Y-%m-%d')
    broadcast_time = datetime.strptime(html_element.xpath('./@data-airtime')[0], '%H')
    broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())
    broadcast_show = show(html_element)

    # Get accurate download information for the RSS Enclosure
    download_url = html_element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()
    download_headers = requests.head(download_url).headers

    return IndividualPodcast(title=broadcast_show.name,
                             description=(broadcast_show.description if broadcast_show.description else ""),
                             broadcast_date=broadcast_datetime.strftime("%a, %d %b %Y %H:%M:%S +0000"),
                             web_url=(broadcast_show.web_url if broadcast_show.web_url else download_url),
                             enclosure_url=download_url,
                             enclosure_content_length=download_headers.get("content-length"),
                             enclosure_content_type=download_headers.get("content-type"),
                             show=broadcast_show)


def podcasts(scrape_url):
    """
    :param scrape_url: Webpage URL to scrape for Podcasts
    :return: An iterable of scraped Podcasts

    :rtype: [IndividualPodcast]
    """
    logging.info("Fetching podcast items from {0}".format(scrape_url))
    podcasts_page = html(requests.get(scrape_url).content)
    #TODO: scrape more than the front page
    return [podcast(div) for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]')]
