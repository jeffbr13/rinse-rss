from os import environ as env

DEBUG = env.get('DEBUG', False)
SQLALCHEMY_DATABASE_URI = env.get('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/rinse-rss.sqlite')
