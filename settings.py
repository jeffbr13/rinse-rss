# -*- coding: utf-8 -*-
from os import environ as env

DEBUG = bool(env.get('DEBUG', False))
SERVER_NAME = env.get('SERVER_NAME', '127.0.0.1:5000')
SQLALCHEMY_DATABASE_URI = env.get('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/rinse-rss.sqlite')


# podcast feed template variables

RSS_TITLE = "Rinse FM"
RSS_SUBTITLE = "London's favorite pirate radio station."
RSS_DESCRIPTION = """
London's favorite pirate radio station now available in unofficial podcast format.

Rinse FM is uniquely placed at the hub of the Capitalʼs thriving British underground music community, demonstrating throughout 18 years of broadcasting that they provide a vital, unique and exceptionally successful, grass-roots gateway into broadcast radio and the wider music industry.

Rinseʼs DJs and MCs have won Mercury Music Prize awards, with nominations for numerous others, gold discs in recognition of sales, and widespread critical acclaim. In stark contrast to the homogenized radio landscape Rinse FM seeks to champion the diverse needs of young London and those passionate about youth-orientated music culture, currently showcasing genres typically referred to as Dubstep, UK Funky and Grime while interacting with and influencing those scenes. Rinseʼs fiercely grass-roots broadcasting ethos engages massively under-represented communities, especially 15-24 year olds.
"""
RSS_KEYWORDS = "Rinse FM, rinse, grime, garage, dubstep, house, deep house, techno, urban, music"
RSS_CATEGORY = "Music"     # http://www.apple.com/itunes/podcasts/specs.html#categories

RSS_OWNER = "Rinse FM"
RSS_COPYRIGHT = "Rinse FM 2014"

RSS_LANGUAGE = "en-gb"

RSS_PODCAST_OWNER = "Ben Jeffrey"
RSS_PODCAST_OWNER_EMAIL = "mail@benjeffrey.net"

RSS_PODCAST_SCRAPE_URL = "http://rinse.fm/podcasts/"
RSS_SHOW_SCRAPE_URL = "http://rinse.fm/family/"
RSS_WEB_URL = "http://rinse.fm/podcasts/"
