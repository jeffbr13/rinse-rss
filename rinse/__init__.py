#!python3
import logging

import requests
from flask.ext.script import Command
from lxml.html import fromstring as html
from sqlalchemy.orm import sessionmaker

from rinse.models import db, PodcastEpisode, Show
from settings import RSS_PODCAST_EPISODE_SCRAPE_URL
from settings import RSS_SHOW_SCRAPE_URL


def scrape_podcast_episodes(scrape_url):
    """
    :param scrape_url: URL of webpage to scrape for IndividualPodcasts
    :return: a collection of scraped Podcasts

    :rtype: [PodcastEpisode]
    """
    logging.info("Fetching podcast data from {0}".format(scrape_url))
    podcasts_page = html(requests.get(scrape_url).content)
    # TODO: scrape more than the front page
    episodes = []
    for div in podcasts_page.xpath('//div[contains(@class, "podcast-list-item")]'):
        try:
            episodes.append(PodcastEpisode(div))
        except Exception as e:
            logging.error(e)
    return episodes


def scrape_shows(scrape_url):
    """
    :param scrape_url: URL of webpage to scrape for RecurringShows
    :return: a collection of RecurringShows
    :rtype: [Show]
    """
    logging.info("Fetching shows data from {}".format(scrape_url))
    shows_page = html(requests.get(scrape_url).content)
    hrefs = shows_page.xpath("//a[contains(@href, 'artist')]/@href")
    recurring_shows = []
    for href in hrefs:
        try:
            recurring_shows.append(Show(href))
        except Exception as e:
            logging.error(e)
            pass
    return recurring_shows


class ScrapeCommand(Command):
    "Scrapes Rinse FM for new episodes and shows then saves to database."

    def run(self):
        session = sessionmaker(bind=db.engine)()

        for show in scrape_shows(RSS_SHOW_SCRAPE_URL):
            logging.info("Merging %s into database…" % show)
            session.merge(show)

        for podcast in scrape_podcast_episodes(RSS_PODCAST_EPISODE_SCRAPE_URL):
            logging.info("Merging %s into database…" % podcast)

            if podcast.show_slug and not Show.query.get(podcast.show_slug):
                logging.info("Show for %s doesn't exist in database, scraping from website…" % podcast)
                try:
                    show = Show('http://rinse.fm/artists/{}/'.format(podcast.show_slug))
                    logging.info("Merging {} into database for {}".format(show, podcast))
                    session.merge(show)
                    session.merge(podcast)
                except Exception as e:
                    logging.warning("Skipping podcast {}, couldn't create show".format(podcast), e)

        session.commit()
