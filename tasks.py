import logging
from datetime import timedelta
from os import environ

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yaml import load as yaml_load

from rinse import IndividualPodcast, RecurringShow, scrape_podcasts, scrape_shows


logging.basicConfig(level=logging.DEBUG) if bool(environ.get('DEBUG')) else logging.basicConfig(level=logging.INFO)
app = Celery('tasks', broker='redis://localhost')
with open('config.yaml') as f:
    podcasts_feed_config = yaml_load(f)["PODCASTS_FEED"]

db_engine = create_engine(environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://"))
DatabaseSession = sessionmaker(bind=db_engine)


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
    for podcast in scrape_podcasts(podcasts_feed_config['podcast_scrape_url']):
        logging.info("Merging %s into database…" % podcast)
        db_session.merge(podcast)
    db_session.commit()


if __name__ == "__main__":
    app.worker_main()
