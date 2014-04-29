#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
from datetime import datetime
import logging
from os import environ

from flask import Flask, render_template, request, jsonify, abort
import requests
from yaml import load

import rinse
from groupby_all import groupby_all


logging.basicConfig(level=logging.DEBUG)

SERVER = Flask(__name__)

SERVER_URL = 'http://rinse-rss.benjeffrey.com'
ARTWORK_HREF = '/artwork'
CONFIGURATION = None
PODCAST_ITEMS = None
PODCAST_ITEMS_BY_ARTIST = None
LAST_REFRESH = None


def init_configuration():
    with open('feed-configuration.yaml') as f:
        return load(f)


def get_podcast_items(configuration):
    LAST_REFRESH = datetime.now()
    return rinse.podcast_items(configuration)


@SERVER.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html.j2', artists=PODCAST_ITEMS_BY_ARTIST.keys())


@SERVER.route('/rss.xml')
def main_feed():
    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/rss.xml'),
                           feed_configuration=CONFIGURATION,
                           podcast_items=PODCAST_ITEMS)


@SERVER.route('/<artist_name>.rss.xml')
def artist_podcast_feed(artist_name):
    if not artist_name in PODCAST_ITEMS_BY_ARTIST:
        abort(404)

    configuration=CONFIGURATION.copy()
    configuration['title'] = (artist_name + ' on ' + configuration['title'])

    if PODCAST_ITEMS_BY_ARTIST[artist_name][0].artist.url:
        configuration['url'] = PODCAST_ITEMS_BY_ARTIST[artist_name][0].artist.url

    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/' + artist_name + '.rss.xml'),
                           feed_configuration=configuration,
                           podcast_items=PODCAST_ITEMS_BY_ARTIST[artist_name])


@SERVER.route(ARTWORK_HREF)
def podcast_artwork():
    """Serve the podcast artwork image."""
    return SERVER.send_static_file('artwork.png')


if __name__ == '__main__':

    CONFIGURATION = init_configuration()
    CONFIGURATION['thumbnail_url'] = SERVER_URL + ARTWORK_HREF

    PODCAST_ITEMS = sorted(get_podcast_items(CONFIGURATION), key=lambda item: item.pub_date)
    PODCAST_ITEMS_BY_ARTIST = dict(groupby_all(PODCAST_ITEMS, key=lambda item: item.artist.name))
    print(PODCAST_ITEMS_BY_ARTIST)

    logging.info('Starting server...')
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    SERVER.run(host='0.0.0.0', port=port, debug=True)

