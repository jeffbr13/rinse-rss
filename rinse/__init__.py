#!python3
import logging

import requests
from lxml.html import fromstring as html

from rinse.models import db, PodcastEpisode, Show


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
