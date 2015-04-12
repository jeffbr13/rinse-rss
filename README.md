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


Deployment
----------

1) check-out this repository,
2) copy the Upstart service definition to the required folder,
3) copy and link the Nginx reverse-proxy configuration,
4) check it works:

```sh
git clone https://github.com/jeffbr13/rinse-rss.git /opt/rinse-rss
cp /opt/rinse-rss/upstart.conf /etc/init/rinse-rss.conf
cp /opt/rinse-rss/nginx.conf /etc/nginx/sites-available/rinse-rss
ln -s /etc/nginx/sites-available/rinse-rss /etc/nginx/sites-enabled/rinse-rss
service rinse-rss start
```


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
