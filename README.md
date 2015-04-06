rinse-rss
=========

Unofficial Rinse FM RSS podcast feeds available at <http://rinse.benjeffrey.net>.

`rinse-rss`'s UI is provided by [Flask-Script](http://flask-script.readthedocs.org/en/latest/):

```sh
python server.py run    # to run the webserver
```


database maintenance
--------------------

Database migrations are managed through [Flask-Migrate](https://flask-migrate.readthedocs.org).

```sh
python server.py db migrate     # to create a database migration
python server.py db update      # to apply database migrations
```
