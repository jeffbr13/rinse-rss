rinse-rss
=========

Unofficial Rinse FM RSS podcast feeds available at <http://rinse.benjeffrey.net>.

`rinse-rss`'s UI is provided by [Flask-Script](http://flask-script.readthedocs.org/en/latest/):

```sh
python server.py run    # to run the webserver
```


scraping data
-------------

`rinse-rss` uses a [Celery](http://www.celeryproject.org) worker to scrape the Rinse FM website,
and update the database in the background every quarter-hour.

```sh
celery -A tasks worker -B -l info   # run foreground worker

celery multi start -A tasks worker -B -l info   # run background worker
celery multi stopwait -A tasks worker -B -l info    # stop background worker
```


database maintenance
--------------------

Database migrations are managed through [Flask-Migrate](https://flask-migrate.readthedocs.org).

```sh
python server.py db migrate     # to create a database migration
python server.py db upgrade      # to apply database migrations
```
