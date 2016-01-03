#!python3
# -*- coding: utf-8 -*-
"""HTTP server for Rinse podcast feed"""
import os.path
import yaml

from flask import Flask, render_template, send_from_directory, make_response
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from rinse import db, IndividualPodcast, RecurringShow


app = Flask(__name__)
app.config.from_object('settings')

with open("feed.yml") as f:
    app.config.update(PODCASTS_FEED=yaml.load(f))

db.init_app(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)


@app.route('/')
def index():
    """Index page of all podcast feeds.
    """
    return render_template('index.html', shows=sorted(RecurringShow.query.all(), key=lambda x: x.slug))


@app.route('/podcasts')
def full_feed():
    """RSS feed of all podcasts"""
    response = make_response(render_template('rss.xml',
                                             feed_url=(app.config['PODCASTS_FEED']['server_url'] + '/podcasts'),
                                             feed_configuration=app.config['PODCASTS_FEED'],
                                             podcasts=sorted(IndividualPodcast.query.all(),
                                                             key=(lambda x: x.broadcast_date),
                                                             reverse=True)))
    response.mimetype = "application/rss+xml"
    return response


@app.route('/show/<show_slug>.rss')
def recurring_show_feed(show_slug):
    """RSS feed of a single show"""
    show = RecurringShow.query.filter_by(slug=show_slug).first_or_404()

    feed_configuration = app.config['PODCASTS_FEED'].copy()
    feed_configuration["title"] = show.name + " on " + feed_configuration["title"]

    if show.description:
        feed_configuration['description'] = show.description
    if show.web_url:
        feed_configuration['url'] = show.web_url


    response = make_response(render_template('rss.xml',
                                             feed_url=(app.config['PODCASTS_FEED']['server_url'] + '/show/' + show_slug + '.rss'),
                                             feed_configuration=feed_configuration,
                                             podcasts=sorted(IndividualPodcast.query.filter_by(show_slug=show_slug),
                                                             key=(lambda x: x.broadcast_date),
                                                             reverse=True)))
    response.mimetype = "application/rss+xml"
    return response


@app.route('/artwork')
def podcast_artwork():
    """
    Serve PNG logo image as Rinse's website logo is SVG.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'artwork.png', mimetype='image/png')


@app.route('/favicon.ico')
def favicon():
    """
    Serve ICO favicon logo.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    manager.run()
