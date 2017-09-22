import logging
from datetime import datetime

import pytz
import requests
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from lxml import html

from .models import PodcastEpisode


logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute='*/15'))
def scrape_podcast_page(page=1):
    scrape_url = 'http://rinse.fm/podcasts/?page=%s' % page
    logging.info("Fetching podcasts from <%s>…".format(scrape_url))
    http_session = requests.Session()
    http_session.headers.update({'User-Agent': 'Mozilla/5.0'})  # don't get blocked
    podcasts_page = html.fromstring(http_session.get(scrape_url).content)
    for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]'):
        try:
            slug = div.get('id')
            title = div.find('.//h3').text_content().strip()
            listen_el = div.xpath('.//div[contains(@class, "listen")]')[0]
            broadcast_day = datetime.strptime(listen_el.find('./a').get('data-air-day'), '%Y-%m-%d')
            broadcast_time = datetime.strptime(listen_el.find('./a').get('data-airtime'), '%H')
            broadcast_date = datetime.combine(broadcast_day.date(), broadcast_time.time()).astimezone(tz=pytz.UTC)
            audio_url = div.xpath('.//a[contains(@href, "http://podcast.dgen.net/rinsefm/podcast/")]/@href')[0]
            audio_response = http_session.head(audio_url)
            audio_response.raise_for_status()
            logger.info('Updating/creating podcast…')
            episode, created = PodcastEpisode.objects.update_or_create(
                slug=slug,
                defaults=dict(
                    title=title,
                    broadcast_date=broadcast_date,
                    audio_url=audio_url,
                    audio_content_length=audio_response.headers['Content-Length'],
                    audio_content_type=audio_response.headers['Content-Type'],
                )
            )
            logger.info(('Created %s.' if created else 'Updated %s.') % episode)
        except:
            logger.exception('Could not scrape podcast:')
    logger.info('Scraped podcasts from <%s>.', scrape_url)


def scrape_podcast_pages(pages):
    for p in range(1, pages + 1):
        scrape_podcast_page(p)
