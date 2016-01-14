rinse-rss
=========

Unofficial Rinse FM RSS podcast feeds available at <http://rinse.benjeffrey.net>.

Run with:

```sh
docker-compose up
```


Running Individual Components
-----------------------------

### Webserver


```sh
docker-compose up web
# or:
python manage.py runserver
```

### Scrape Worker


```sh
docker-compose up scrape
# or:
python manage.py scrape
```


Debugging
---------

Set `DEBUG` environment variable.


Database Maintenance
--------------------

Database migrations are managed through [Flask-Migrate](https://flask-migrate.readthedocs.org).

```sh
python manage.py db migrate                         # create database migration
docker-compose run web python manage.py db upgrade  # apply migrations
```
