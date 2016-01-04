from datetime import datetime
import logging

from flask.ext.sqlalchemy import SQLAlchemy
from lxml.html import fromstring as html
import requests


db = SQLAlchemy()


class PodcastEpisode(db.Model):
    guid = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200))
    broadcast_datetime = db.Column(db.DateTime)
    enclosure_url = db.Column(db.String(200))
    enclosure_content_length = db.Column(db.Integer)
    enclosure_content_type = db.Column(db.String(100))
    show_slug = db.Column(db.String(200), db.ForeignKey("show.slug"), nullable=True)

    def __init__(self,
                 html_element=None,
                 title=None,
                 broadcast_datetime=None,
                 enclosure_url=None,
                 enclosure_content_length=None,
                 enclosure_content_type=None,
                 show_slug=None):
        """
        Scrape PodcastEpisode information from html_element if given,
        otherwise use passed-through values.

        :type html_element: lxml.html.HtmlElement
        """
        if html_element:
            logging.info('Initialising Podcast from HTML element')
            try:
                broadcast_date = datetime.strptime(
                        html_element.xpath('.//div[contains(@class, "listen")]/a/@data-air-day')[0],
                        '%Y-%m-%d')
                broadcast_time = datetime.strptime(
                        html_element.xpath('.//div[contains(@class, "listen")]/a/@data-airtime')[0],
                        '%H')
                broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())
                title = " ".join(html_element.xpath(".//h3//text()")).strip()
                show_url = html_element.xpath(".//h3/a/@href")
            except IndexError as e:
                logging.error("likely XPath query error due to webpage misrendering/misloading", e)
                raise
            try:
                show_slug = Show.parse_slug(show_url)
            except Exception as e:
                logging.info('Could not parse show slug', e)
                show_slug = None

            # Get accurate download information for the RSS Enclosure
            enclosure_url = html_element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()
            download_headers = requests.head(enclosure_url).headers
            enclosure_content_length = download_headers.get('content-length')
            enclosure_content_type = download_headers.get('content-type')

        self.guid = enclosure_url
        self.title = title
        self.broadcast_datetime = broadcast_datetime
        self.enclosure_url = enclosure_url
        self.enclosure_content_length = enclosure_content_length
        self.enclosure_content_type = enclosure_content_type
        self.show_slug = show_slug

    def __repr__(self):
        return "<PodcastEpisode: %s>" % self.guid


class Show(db.Model):
    slug = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    web_url = db.Column(db.String(200))
    podcasts = db.relationship("PodcastEpisode", backref=db.backref("show"))

    @staticmethod
    def parse_slug(web_url):
        """Split unique Show slug from URL"""
        try:
            return web_url.rsplit('/', 2)[-2]
        except AttributeError as e:
            logging.debug('retrying slug split in the case that XPath returned a list', e)
            return Show.parse_slug(web_url[0])

    def __init__(self, web_url, slug=None, name=None, description=None):
        if not (slug and name and description):
            logging.info('Scraping Show from URL {}'.format(web_url))
            slug = Show.parse_slug(web_url)
            show_page = html(requests.get(web_url).content)
            try:
                base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'
                name = show_page.xpath(base_xpath + '/div/h2//text()')[0]
                description = '\n\n'.join(show_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
            except IndexError as e:
                logging.error("likely XPath query error due to webpage misloading/misrendering", e)
                raise
            logging.info('Successfully scraped Show from %s' % web_url)

        self.slug = slug
        self.name = name
        self.description = description
        self.web_url = web_url

    def __repr__(self):
        return "<Show: %s>" % self.slug
