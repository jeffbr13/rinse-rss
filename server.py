#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
from datetime import datetime, timedelta
from os import environ

from flask import Flask, render_template, send_from_directory
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy

from yaml import load as yaml_load


import rinse
from helpers import groupby_all


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

with open('config.yaml') as f:
    app.config.update(yaml_load(f))

app.config.update(
    DEBUG=bool(environ.get('DEBUG', False)),
    SQLALCHEMY_DATABASE_URI=(environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://:memory:")))

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)


class IndividualPodcast(db.Model):
    guid = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    broadcast_date = db.Column(db.DateTime)
    web_url = db.Column(db.String(200))

    enclosure_url = db.Column(db.String(200))
    enclosure_content_length = db.Column(db.Integer)
    enclosure_content_type = db.Column(db.String(100))

    show_slug = db.Column(db.String(200), db.ForeignKey("recurring_show.slug"))

    def __init__(self, title, description, broadcast_date, web_url,
                       enclosure_url, enclosure_content_length, enclosure_content_type,
                       show):
        self.title = title
        self.description = description
        self.broadcast_date = broadcast_date
        self.web_url = web_url
        self.enclosure_url = enclosure_url
        self.enclosure_content_length = enclosure_content_length
        self.enclosure_content_type = enclosure_content_type
        self.show_slug = show.slug
        self.guid = self.enclosure_url

    def __repr__(self):
        return "<IndividualPodcast: %s>" % self.guid


class RecurringShow(db.Model):
    slug = db.Column(db.String(200), primary_key=True)


    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    web_url = db.Column(db.String(200))

    podcasts = db.relationship("IndividualPodcast", backref=db.backref("show"))

    def __init__(self, slug, name, description, web_url):
        self.slug = slug
        self.name = name
        self.description = description
        self.web_url = web_url

    def __repr__(self):
        return "<RecurringShow: %s>" % self.slug


@app.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html', shows=RecurringShow.query.all())


@app.route('/podcasts')
def full_feed():
    return render_template('rss.xml',
                           feed_url=('http://' + app.config['PODCASTS_FEED']['server_url'] + '/podcasts'),
                           feed_configuration=app.config['PODCASTS_FEED'],
                           podcasts=IndividualPodcast.query.all())


@app.route('/show/<show_slug>.rss')
def recurring_show_feed(show_slug):
    show = RecurringShow.query.filter(slug=show_slug).first_or_404()

    feed_configuration = app.config['PODCASTS_FEED'].copy()
    feed_configuration["title"] = show.name + " on " + feed_configuration["title"]

    if show.description:
        feed_configuration['description'] = show.description
    if show.web_url:
        feed_configuration['url'] = show.web_url

    return render_template('rss.xml',
                           feed_url=('http://' + app.config['PODCASTS_FEED']['server_url'] + '/show/' + show_slug + '.rss'),
                           feed_configuration=feed_configuration,
                           podcasts=IndividualPodcast.query.filter(show_slug=show.slug))


@app.route('/artwork')
def podcast_artwork():
    """
    Rinse FM's website logo is an SVG (good for them!) which I used to create a PNG, served here as a static asset.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@app.route('/favicon.ico')
def favicon():
    """
    I also created a favicon ICO version of the Rinse FM logo, served here as a static asset.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@manager.command
def run():
    """
    Binds to $PORT if defined, otherwise default to 5000.
    """
    port = int(environ.get('PORT', 5000))
    logging.debug('Launching Flask app...')
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    # Respond to manager commands (just "db" and "run" at this point) when run directly
    manager.run()
