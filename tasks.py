import logging
import yaml
from datetime import timedelta
from os import environ

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rinse import Show, scrape_podcast_episodes, scrape_shows

# configure logging
logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG')) else logging.basicConfig(level=logging.INFO)
# load configuration
with open('feed.yml') as f:
    podcasts_feed_config = yaml.load(f)
# connect to cache and database
app = Celery('tasks', broker=("redis://" + environ.get("REDIS_PORT_6379_TCP_ADDR", "localhost")))
db_engine = create_engine(environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://"))
DatabaseSession = sessionmaker(bind=db_engine)

# Schedule tasks
app.conf.CELERYBEAT_SCHEDULE = {
    'refresh-data-every-quarter-hour': {
        'task': 'tasks.refresh_data',
        'schedule': timedelta(minutes=15),
    },
}
app.conf.CELERY_TIMEZONE = 'UTC'


@app.task(ignore_results=True)
def refresh_data():
    db_session = DatabaseSession()
    logging.info("Scraping show and podcast pages for new material…")
    for show in scrape_shows(podcasts_feed_config["show_scrape_url"]):
        logging.info("Merging %s into database…" % show)
        db_session.merge(show)
    for podcast in scrape_podcast_episodes(podcasts_feed_config['podcast_scrape_url']):
        logging.info("Merging %s into database…" % podcast)
        if podcast.show_slug and not db_session.query(Show).get(podcast.show_slug):
            logging.info("Show for %s doesn't exist in database, scraping from website…" % podcast)
            try:
                show = Show('http://rinse.fm/artists/{}/'.format(podcast.show_slug))
                logging.info("Merging {} into database for {}".format(show, podcast))
                db_session.merge(show)
            except Exception as e:
                logging.error("Skipping podcast, couldn't create show: {}".format(e))
                continue
        db_session.merge(podcast)
    db_session.commit()


if __name__ == "__main__":
    app.worker_main()
