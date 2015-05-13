#!python
# -*- coding: utf-8 -*-
"""Server for rinse.benjeffrey.com"""
import logging
import os.path
import yaml
from os import environ

from flask import Flask, render_template, send_from_directory, make_response
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from rinse import db, IndividualPodcast, RecurringShow


##### App Configuration ################################################################################################

logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG', False)) else logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

with open("feed.yml") as f:
    app.config.update(PODCASTS_FEED=yaml.load(f))

app.config.update(
    DEBUG=bool(environ.get('DEBUG', False)),
    SQLALCHEMY_DATABASE_URI=(environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://")))

db.init_app(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)


##### Routes ###########################################################################################################

@app.route('/')
def index():
    """Serve an index of all podcast feed URLs.
    """
    return render_template('index.html', shows=sorted(RecurringShow.query.all(), key=lambda x: x.slug))


@app.route('/podcasts')
def full_feed():
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
    #TODO: generate custom image for each show
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


##### UI Commands ######################################################################################################

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
