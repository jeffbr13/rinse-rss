from datetime import datetime
import logging

from flask.ext.sqlalchemy import SQLAlchemy
from furl import furl
from lxml.html import fromstring as html, HtmlElement
import requests


http_session = requests.Session()
http_session.headers.update({'User-Agent': 'Mozilla/5.0'})

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
                 html_element: HtmlElement =None,
                 title=None,
                 broadcast_datetime=None,
                 enclosure_url=None,
                 enclosure_content_length=None,
                 enclosure_content_type=None,
                 show_slug=None):
        """
        Scrape PodcastEpisode information from html_element if given,
        otherwise use passed-through values.
        """
        if html_element:
            logging.info('Parsing PodcastEpisode from HTML element…')
            try:
                enclosure_url = html_element.xpath('./div/div[@class="download icon"]/a/@href')[0].strip()

                broadcast_date = datetime.strptime(
                        html_element.xpath('.//div[contains(@class, "listen")]/a/@data-air-day')[0],
                        '%Y-%m-%d')
                broadcast_time = datetime.strptime(
                        html_element.xpath('.//div[contains(@class, "listen")]/a/@data-airtime')[0],
                        '%H')
                broadcast_datetime = datetime.combine(broadcast_date.date(), broadcast_time.time())
                title = " ".join(html_element.xpath(".//h3//text()")).strip()
            except IndexError:
                logging.warning("Failed parsing PodcastEpisode.", exc_info=True)
                raise

            try:
                show_url = html_element.xpath(".//h3/a/@href")
                if isinstance(show_url, list):
                    # in case the XPath returned multiple "href"s
                    show_url = show_url[0]
                show_slug = Show.parse_slug(furl(show_url)) if show_url else None
            except IndexError:
                logging.info("Could not find Show URL for PodcastEpisode <%s>.", enclosure_url)

            # Get accurate download information for the RSS Enclosure
            download_headers = http_session.head(enclosure_url).headers
            enclosure_content_length = download_headers.get('content-length')
            enclosure_content_type = download_headers.get('content-type')

            logging.info('Scraped PodcastEpisode <%s>.', enclosure_url)

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
    def parse_slug(url: furl):
        """Get the unique slug from a Show's URL"""
        return url.path.segments[-2]

    def __init__(self, url, slug=None, name=None, description=None):
        if not (slug and name and description):
            logging.info('Scraping Show from <%s>…', url)
            slug = Show.parse_slug(furl(url))
            show_page = html(http_session.get(url).content)
            try:
                base_xpath = '/html/body/div[@id="wrapper"]/div[@id="container"]/div[contains(@class, "rounded")]/div'
                name = show_page.xpath(base_xpath + '/div/h2//text()')[0]
                description = '\n\n'.join(show_page.xpath(base_xpath + '/div[contains(@class, "entry")]/p//text()'))
            except IndexError:
                logging.error("Failed scraping Show name on show page <%s>.", url, exc_info=True)
                raise
            logging.info('Scrape Show from <%s>.' % url)

        self.slug = slug
        self.name = name
        self.description = description
        self.web_url = url

    def __repr__(self):
        return "<Show: %s>" % self.slug
