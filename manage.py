#!python3
# -*- coding: utf-8 -*-
"""HTTP server for Rinse podcast feed"""
import logging
import os.path

from flask import Flask, render_template, send_from_directory, make_response
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from rinse import db, Show, scrape_shows, scrape_podcast_episodes, ScrapeCommand
from rinse.models import PodcastEpisode, Show
from settings import RSS_SHOW_SCRAPE_URL, RSS_PODCAST_EPISODE_SCRAPE_URL

app = Flask(__name__)
app.config.from_object('settings')

db.init_app(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)
manager.add_command("scrape", ScrapeCommand)


@app.route('/')
def serve_index_page():
    return render_template('index.html', shows=sorted(Show.query.all(), key=lambda x: x.slug))


@app.route('/podcasts')
def serve_all_shows_feed():
    response = make_response(render_template('rss.xml',
                                             self_link=app.config['SERVER_NAME'] + '/podcasts',
                                             web_link=app.config['RSS_WEB_URL'],
                                             title=app.config['RSS_TITLE'],
                                             subtitle=app.config['RSS_SUBTITLE'],
                                             description=app.config['RSS_DESCRIPTION'],
                                             keywords=app.config['RSS_KEYWORDS'],
                                             language=app.config['RSS_LANGUAGE'],
                                             owner=app.config['RSS_OWNER'],
                                             copyright=app.config['RSS_COPYRIGHT'],
                                             podcast_owner=app.config['RSS_PODCAST_OWNER'],
                                             podcast_owner_email=app.config['RSS_PODCAST_OWNER_EMAIL'],
                                             thumbnail_url=(app.config['SERVER_NAME'] + '/artwork'),
                                             category=app.config['RSS_CATEGORY'],
                                             podcasts=sorted(PodcastEpisode.query.all(),
                                                             key=(lambda p: p.broadcast_date),
                                                             reverse=True)))
    response.mimetype = "application/rss+xml"
    return response


@app.route('/show/<show_slug>.rss')
def serve_single_show_feed(show_slug):
    show = Show.query.filter_by(slug=show_slug).first_or_404()
    response = make_response(render_template('rss.xml',
                                             self_link=app.config['SERVER_NAME'] + '/show/' + show_slug + '.rss',
                                             web_link=show.web_url,
                                             title=(show.name + ' on ' + app.config['RSS_TITLE']),
                                             subtitle=app.config['RSS_SUBTITLE'],
                                             description=show.description,
                                             keywords=app.config['RSS_KEYWORDS'],
                                             language=app.config['RSS_LANGUAGE'],
                                             owner=app.config['RSS_OWNER'],
                                             copyright=app.config['RSS_COPYRIGHT'],
                                             podcast_owner=app.config['RSS_PODCAST_OWNER'],
                                             podcast_owner_email=app.config['RSS_PODCAST_OWNER_EMAIL'],
                                             thumbnail_url=(app.config['SERVER_NAME'] + '/artwork'),
                                             category=app.config['RSS_CATEGORY'],
                                             podcasts=sorted(PodcastEpisode.query.filter_by(show_slug=show_slug),
                                                             key=(lambda p: p.broadcast_date),
                                                             reverse=True)))
    response.mimetype = "application/rss+xml"
    return response


@app.route('/artwork')
def serve_podcast_artwork():
    """
    Serve PNG logo image as Rinse's website logo is SVG.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@app.route('/favicon.ico')
def serve_favicon():
    """
    Serve ICO favicon logo.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    manager.run()
