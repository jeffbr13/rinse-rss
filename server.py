#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
from datetime import datetime, timedelta
from os import environ

from flask import Flask, render_template, abort, send_from_directory
from yaml import load as yaml_load

import rinse
from helpers import groupby_all


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

with open('config.yaml') as f:
    app.config.update(yaml_load(f))

app.config.update(
    DEBUG=bool(environ.get('DEBUG', False)),
)

PODCASTS = None
PODCASTS_BY_SHOW_WITH_URL = None
SHOWS_WITH_URLS = None
LAST_REFRESH = None


def get_podcasts():
    logging.info('Getting podcast items...')
    LAST_REFRESH = datetime.now()
    return rinse.podcasts(app.config['PODCASTS_FEED']['scrape_url'])


def refresh(podcasts, podcasts_by_show_with_url, shows_with_urls):
    if not LAST_REFRESH or LAST_REFRESH < (datetime.now() - timedelta(minutes=15)):
        logging.info('Refreshing data.')
        podcasts = sorted(get_podcasts(), key=lambda item: item.pub_date)
        podcasts_by_show_with_url = groupby_all([item for item in podcasts if item.show.url],
                                                key=lambda item: item.show.url_safe_name)
        shows_with_urls = sorted(
            [item[0].show for item in podcasts_by_show_with_url.values()],
            key=lambda x: x.name)
        return (podcasts, podcasts_by_show_with_url, shows_with_urls)
    else:
        return podcasts, podcasts_by_show_with_url, shows_with_urls


PODCASTS, PODCASTS_BY_SHOW_WITH_URL, SHOWS_WITH_URLS = refresh(PODCASTS,
                                                               PODCASTS_BY_SHOW_WITH_URL,
                                                               SHOWS_WITH_URLS)

@app.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html', shows=SHOWS_WITH_URLS)


@app.route('/podcasts')
def main_feed():
    return render_template('rss.xml',
                           feed_url=('http://' + app.config['PODCASTS_FEED']['server_url'] + '/podcasts'),
                           feed_configuration=app.config['PODCASTS_FEED'],
                           podcasts=PODCASTS)


@app.route('/show/<show_name>.rss')
def show_podcast_feed(show_name):
    if not show_name in PODCASTS_BY_SHOW_WITH_URL:
        abort(404)

    feed_configuration = app.config['PODCASTS_FEED'].copy()
    feed_configuration['title'] = (PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.name + ' on ' + feed_configuration['title'])

    if PODCASTS_BY_SHOW_WITH_URL[show_name][0].description:
        feed_configuration['description'] = PODCASTS_BY_SHOW_WITH_URL[show_name][0].description

    if PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.url:
        feed_configuration['url'] = PODCASTS_BY_SHOW_WITH_URL[show_name][0].show.url

    return render_template('rss.xml',
                           feed_url=('http://' + app.config['PODCASTS_FEED']['server_url'] + '/show/' + show_name + '.rss'),
                           feed_configuration=feed_configuration,
                           podcasts=PODCASTS_BY_SHOW_WITH_URL[show_name])


@app.route('/artwork')
def podcast_artwork():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    app.run(host='0.0.0.0', port=port)
