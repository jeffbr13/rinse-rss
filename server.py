#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
from datetime import datetime
from os import environ
from urllib.parse import quote as url_quote, unquote as url_unquote

import requests
from flask import Flask, render_template, request, jsonify, abort
from yaml import load as yaml_load

import rinse
from helpers import groupby_all


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

SERVER = Flask(__name__)

SERVER_URL = 'http://rinse-rss.benjeffrey.com'
ARTWORK_HREF = '/artwork'
CONFIGURATION = None
PODCAST_ITEMS = None
PODCAST_ITEMS_BY_ARTIST_WITH_URL = None
ARTISTS_WITH_URLS = None
LAST_REFRESH = None


def init_configuration():
    logging.info('Loading configuration...')
    with open('feed-configuration.yaml') as f:
        return yaml_load(f)


def get_podcast_items(configuration):
    logging.info('Getting podcast items...')
    LAST_REFRESH = datetime.now()
    return rinse.podcast_items(configuration)


@SERVER.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html.j2', artists=ARTISTS_WITH_URLS)


@SERVER.route('/rss.xml')
def main_feed():
    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/rss.xml'),
                           feed_configuration=CONFIGURATION,
                           podcast_items=PODCAST_ITEMS)


@SERVER.route('/feed/<artist_name>.rss')
def artist_podcast_feed(artist_name):
    if not artist_name in PODCAST_ITEMS_BY_ARTIST_WITH_URL:
        abort(404)

    feed_configuration=CONFIGURATION.copy()
    feed_configuration['title'] = (PODCAST_ITEMS_BY_ARTIST_WITH_URL[artist_name][0].artist.name + ' on ' + feed_configuration['title'])

    if PODCAST_ITEMS_BY_ARTIST_WITH_URL[artist_name][0].artist.url:
        feed_configuration['url'] = PODCAST_ITEMS_BY_ARTIST_WITH_URL[artist_name][0].artist.url

    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/feed/' + artist_name + '.rss'),
                           feed_configuration=feed_configuration,
                           podcast_items=PODCAST_ITEMS_BY_ARTIST_WITH_URL[artist_name])


@SERVER.route(ARTWORK_HREF)
def podcast_artwork():
    """Serve the podcast artwork image."""
    return SERVER.send_static_file('artwork.png')


if __name__ == '__main__':
    logging.info('Starting server...')

    CONFIGURATION = init_configuration()
    CONFIGURATION['thumbnail_url'] = SERVER_URL + ARTWORK_HREF

    PODCAST_ITEMS = sorted(get_podcast_items(CONFIGURATION), key=lambda item: item.pub_date)
    PODCAST_ITEMS_BY_ARTIST_WITH_URL = groupby_all([item for item in PODCAST_ITEMS if item.artist.url],
                                                   key=lambda item: item.artist.url_safe_name)
    ARTISTS_WITH_URLS = [item[0].artist for item in PODCAST_ITEMS_BY_ARTIST_WITH_URL.values()]

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    SERVER.run(host='0.0.0.0', port=port, debug=bool(environ.get('DEBUG', False)))


