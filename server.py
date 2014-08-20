#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
from datetime import datetime, timedelta
from os import environ
from urllib.parse import quote as url_quote, unquote as url_unquote

import requests
from flask import Flask, render_template, request, jsonify, abort, send_from_directory
from yaml import load as yaml_load

import rinse
from helpers import groupby_all


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

SERVER = Flask(__name__)

CONFIGURATION = None
PODCASTS = None
PODCASTS_BY_SHOW_WITH_URL = None
SHOWS_WITH_URLS = None
LAST_REFRESH = None


def load_configuration():
    logging.info('Loading configuration...')
    with open('feed-configuration.yaml') as f:
        return yaml_load(f)


def get_podcasts(configuration):
    logging.info('Getting podcast items...')
    LAST_REFRESH = datetime.now()
    return rinse.podcasts(configuration['scrape_url'])


def refresh(configuration, podcasts, podcasts_by_show_with_url, shows_with_urls):
    if not LAST_REFRESH or LAST_REFRESH < (datetime.now() - timedelta(minutes=15)):
        logging.info('Refreshing data.')
        podcasts = sorted(get_podcasts(configuration), key=lambda item: item.pub_date)
        podcasts_by_show_with_url = groupby_all([item for item in podcasts if item.show.url],
                                                key=lambda item: item.show.url_safe_name)
        shows_with_urls = sorted(
            [item[0].show for item in podcasts_by_show_with_url.values()],
            key=lambda x: x.name)
        return (podcasts, podcasts_by_show_with_url, shows_with_urls)
    else:
        return podcasts, podcasts_by_show_with_url, shows_with_urls


@SERVER.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html', shows=SHOWS_WITH_URLS)


@SERVER.route('/podcasts')
def main_feed():
    return render_template('rss.xml',
                           feed_url=(CONFIGURATION['server_url'] + '/rss'),
                           feed_configuration=CONFIGURATION,
                           podcasts=PODCASTS)


@SERVER.route('/show/<show_name>.rss')
def show_podcast_feed(show_name):
    if not show_name in PODCASTS_BY_SHOW_WITH_URL:
        abort(404)

    feed_configuration = CONFIGURATION.copy()
    feed_configuration['title'] = (PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.name + ' on ' + feed_configuration['title'])

    if PODCASTS_BY_SHOW_WITH_URL[show_name][0].description:
        feed_configuration['description'] = PODCASTS_BY_SHOW_WITH_URL[show_name][0].description

    if PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.url:
        feed_configuration['url'] = PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.url

    return render_template('rss.xml',
                           feed_url=(CONFIGURATION['server_url'] + '/show/' + show_name + '.rss'),
                           feed_configuration=feed_configuration,
                           podcasts=PODCASTS_BY_SHOW_WITH_URL[show_name])


@SERVER.route('/artwork')
def podcast_artwork():
    return send_from_directory(os.path.join(SERVER.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@SERVER.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(SERVER.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    logging.info('Starting server...')

    CONFIGURATION = load_configuration()
    PODCASTS, PODCASTS_BY_SHOW_WITH_URL, SHOWS_WITH_URLS = refresh(CONFIGURATION,
                                                                   PODCASTS,
                                                                   PODCASTS_BY_SHOW_WITH_URL,
                                                                   SHOWS_WITH_URLS)

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    SERVER.run(host='0.0.0.0', port=port, debug=bool(environ.get('DEBUG', False)))
