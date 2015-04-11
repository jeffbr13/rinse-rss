rinse-rss
=========

Unofficial Rinse FM RSS podcast feeds available at <http://rinse.benjeffrey.net>.

`rinse-rss`'s UI is provided by [Flask-Script](http://flask-script.readthedocs.org/en/latest/).

We've recently moved to a [Docker Compose](http://docs.docker.com/compose/) environment.
The application stack is launched with:

```sh
docker-compose up
```

Configuration is in `docker-compose.yml`.


Running Individual Components
-----------------------------

### Webserver


```sh
docker-compose up webserver     # to run the webserver in it's Docker container, or:
python server.py run            # to run the webserver locally
```

### Scrape Worker

`rinse-rss` uses a [Celery](http://www.celeryproject.org) worker to scrape the Rinse FM website,
and update the database in the background every quarter-hour.

```sh
docker-compose up worker    # run worker in Docker container

celery worker --app=tasks --beat --loglevel=                # run foreground worker

celery multi start --app=tasks --beat --loglevel=debug      # run background worker
celery multi stopwait --app=tasks --beat --loglevel=debug   # stop background worker
```


Debugging
---------

- `web` container: set the `DEBUG` environment variable
- `worker` container: set `--loglevel=debug` in the Celery command


Database Maintenance
--------------------

Database migrations are managed through [Flask-Migrate](https://flask-migrate.readthedocs.org).

```sh
python server.py db migrate                         # to create a database migration
docker-compose run web python server.py db upgrade  # to apply database migrations
```
