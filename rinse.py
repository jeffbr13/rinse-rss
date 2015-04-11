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
    broadcast_date = db.Column(db.DateTime)

    enclosure_url = db.Column(db.String(200))
    enclosure_content_length = db.Column(db.Integer)
    enclosure_content_type = db.Column(db.String(100))

    show_slug = db.Column(db.String(200), db.ForeignKey("recurring_show.slug"), nullable=True)

    def __init__(self, title, broadcast_date,
                 enclosure_url, enclosure_content_length, enclosure_content_type,
                 show_slug):
        self.title = title
        self.broadcast_date = broadcast_date
        self.enclosure_url = enclosure_url
        self.enclosure_content_length = enclosure_content_length
        self.enclosure_content_type = enclosure_content_type
        self.show_slug = show_slug
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


def recurring_show_slug(show_url):
    """Given the URL of a RecurringShow, extract the show's unique Rinse FM slug."""
    logging.debug("splitting %s" % show_url)
    try:
        return show_url.rsplit('/', 2)[-2]
    except AttributeError:
        # retry in the case that we get a list (sometimes XPath does this)
        return recurring_show_slug(show_url[0])


def scrape_recurring_show(show_url):
    """
    Scrape show information from a show page.

    :type show_url: str
    :rtype: RecurringShow
    """
    logging.info('Initialising broadcast show information from URL {}'.format(show_url))
    show_slug = show_url.rsplit('/', 2)[-2]
    logging.debug(show_slug)
    show_page = html(requests.get(show_url).content)
    try:
        base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'
        show_name = show_page.xpath(base_xpath + '/div/h2//text()')[0]
        description = '\n\n'.join(show_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
    except IndexError:
        logging.error("IndexError creating show: likely XPath query error due to webpage misrendering/misloading")
        raise
    logging.debug('Successfully extracted show name, description ({}, {}...) from {}'.format(show_name,
                                                                                             description[10],
                                                                                             show_url))
    show = RecurringShow(name=show_name, slug=recurring_show_slug(show_url), description=description, web_url=show_url)
    logging.debug('Successfully initialised %s' % show)
    return show


def scrape_individual_podcast(html_element):
    """
    Build a Podcast using the information in a div.podcast-list-item from the podcasts page.

    :type html_element: lxml.html.HtmlElement
    :rtype: IndividualPodcast
    """
    logging.info('Initialising Podcast from HTML element')
    try:
        broadcast_date = datetime.strptime(html_element.xpath('./@data-air_day')[0], '%Y-%m-%d')
        broadcast_time = datetime.strptime(html_element.xpath('./@data-airtime')[0], '%H')
        broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())
        title = " ".join(html_element.xpath(".//h3//text()")).strip()
        show_url = html_element.xpath(".//h3/a/@href")
    except IndexError:
        logging.error("IndexError creating podcast: likely XPath query error due to webpage misrendering/misloading")
        raise
    logging.debug("title <- %s" % title)
    try:
        show_slug = recurring_show_slug(show_url)
    except:
        show_slug = None

    # Get accurate download information for the RSS Enclosure
    download_url = html_element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()
    download_headers = requests.head(download_url).headers

    return IndividualPodcast(title=title,
                             broadcast_date=broadcast_datetime.strftime("%a, %d %b %Y %H:%M:%S +0000"),
                             enclosure_url=download_url,
                             enclosure_content_length=download_headers.get("content-length"),
                             enclosure_content_type=download_headers.get("content-type"),
                             show_slug=show_slug)


def scrape_podcasts(scrape_url):
    """
    :param scrape_url: URL of webpage to scrape for IndividualPodcasts
    :return: a collection of scraped Podcasts

    :rtype: [IndividualPodcast]
    """
    logging.info("Fetching podcast data from {0}".format(scrape_url))
    podcasts_page = html(requests.get(scrape_url).content)
    #TODO: scrape more than the front page
    individual_podcasts = []
    for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]'):
        try:
            individual_podcasts.append(scrape_individual_podcast(div))
        except Exception as e:
            logging.error(e)
    return individual_podcasts


def scrape_shows(scrape_url):
    """
    :param scrape_url: URL of webpage to scrape for RecurringShows
    :return: a collection of RecurringShows
    :rtype: [RecurringShow]
    """
    logging.info("Fetching shows data from {}".format(scrape_url))
    shows_page = html(requests.get(scrape_url).content)
    hrefs = shows_page.xpath("//a[contains(@class, 'artist')]/@href")
    recurring_shows = []
    for href in hrefs:
        try:
            recurring_shows.append(scrape_recurring_show(href))
        except Exception as e:
            logging.error(e)
            pass
    return recurring_shows

