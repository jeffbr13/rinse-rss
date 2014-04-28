#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
from datetime import datetime
from itertools import groupby
import logging
from os import environ

from flask import Flask, render_template, request, jsonify, redirect, flash
import requests
from yaml import load

import rinse


logging.basicConfig(level=logging.DEBUG)

SERVER = Flask(__name__)

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
    configuration = CONFIGURATION
    return render_template('rss.xml.j2', feed_configuration=CONFIGURATION, podcast_items=PODCAST_ITEMS)


@SERVER.route('/<artist_name>.xml')
def artist_podcast_feed():
    if not artist_name in PODCAST_ITEMS_BY_ARTIST:
        abort(404)

    configuration=CONFIGURATION.copy()
    configuration['title'] = (artist_name + ' on ' + configuration['title'])

    if PODCAST_ITEMS_BY_ARTIST[artist_name][0].artist.url:
        configuration['url'] = PODCAST_ITEMS_BY_ARTIST[artist_name][0].artist.url

    return render_template('rss.xml.j2',
                           feed_configuration=configuration,
                           podcast_items=PODCAST_ITEMS_BY_ARTIST[artist_name])


if __name__ == '__main__':
    CONFIGURATION = init_configuration()
    PODCAST_ITEMS = sorted(get_podcast_items(CONFIGURATION), key=lambda item: item.pub_date)
    PODCAST_ITEMS_BY_ARTIST = dict(groupby(PODCAST_ITEMS, key=lambda item: item.artist.name))

    logging.info('Starting server...')
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    SERVER.run(host='0.0.0.0', port=port, debug=True)


