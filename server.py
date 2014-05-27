#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
from datetime import datetime
from os import environ
from urllib.parse import quote as url_quote, unquote as url_unquote

import requests
from flask import Flask, render_template, request, jsonify, abort, send_from_directory
from yaml import load as yaml_load

import rinse
from helpers import groupby_all


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

SERVER = Flask(__name__)

SERVER_URL = 'http://rinse.benjeffrey.net'
ARTWORK_HREF = '/artwork'
CONFIGURATION = None
SHOWS = None
SHOWS_BY_PRESENTER_WITH_URL = None
PRESENTERS_WITH_URLS = None
LAST_REFRESH = None


def init_configuration():
    logging.info('Loading configuration...')
    with open('feed-configuration.yaml') as f:
        return yaml_load(f)


def get_shows(configuration):
    logging.info('Getting podcast items...')
    LAST_REFRESH = datetime.now()
    return rinse.shows(configuration)


@SERVER.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html.j2', presenters=PRESENTERS_WITH_URLS)


@SERVER.route('/rss.xml')
def main_feed():
    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/rss.xml'),
                           feed_configuration=CONFIGURATION,
                           shows=SHOWS)


@SERVER.route('/feed/<presenter_name>.rss')
def presenter_podcast_feed(presenter_name):
    if not presenter_name in SHOWS_BY_PRESENTER_WITH_URL:
        abort(404)

    feed_configuration=CONFIGURATION.copy()
    feed_configuration['title'] = (SHOWS_BY_PRESENTER_WITH_URL[presenter_name][0].presenter.name + ' on ' + feed_configuration['title'])

    if SHOWS_BY_PRESENTER_WITH_URL[presenter_name][0].presenter.url:
        feed_configuration['url'] = SHOWS_BY_PRESENTER_WITH_URL[presenter_name][0].presenter.url

    return render_template('rss.xml.j2',
                           feed_url=(SERVER_URL + '/feed/' + presenter_name + '.rss'),
                           feed_configuration=feed_configuration,
                           shows=SHOWS_BY_PRESENTER_WITH_URL[presenter_name])


@SERVER.route(ARTWORK_HREF)
def podcast_artwork():
    return send_from_directory(os.path.join(SERVER.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@SERVER.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(SERVER.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@SERVER.route('/typeplate.css')
def typeplate():
  return send_from_directory(os.path.join(SERVER.root_path, 'static'), 'typeplate.css')


if __name__ == '__main__':
    logging.info('Starting server...')

    CONFIGURATION = init_configuration()
    CONFIGURATION['thumbnail_url'] = SERVER_URL + ARTWORK_HREF

    SHOWS = sorted(get_shows(CONFIGURATION), key=lambda item: item.pub_date)
    SHOWS_BY_PRESENTER_WITH_URL = groupby_all([item for item in SHOWS if item.presenter.url],
                                           key=lambda item: item.presenter.url_safe_name)
    PRESENTERS_WITH_URLS = [item[0].presenter for item in SHOWS_BY_PRESENTER_WITH_URL.values()]

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    SERVER.run(host='0.0.0.0', port=port, debug=bool(environ.get('DEBUG', False)))
