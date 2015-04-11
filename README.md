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

Environment Variables
---------------------

* `SQLALCHEMY_DATABASE_URI`: a remote Postgres database is (currently) required. Set `?client_encoding=utf8` for this.
* `DEBUG`: activate the Werkzeug debugger on the webserver and increase logging.


Database Maintenance
--------------------

Database migrations are managed through [Flask-Migrate](https://flask-migrate.readthedocs.org).

```sh
python server.py db migrate     # to create a database migration
python server.py db upgrade      # to apply database migrations
```


Running Individual Components
-----------------------------

### Webserver


```sh
python server.py run            # to run the webserver locally, or:
docker-compose up webserver     # to run the webserver in a Docker container
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
