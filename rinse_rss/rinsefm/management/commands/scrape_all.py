from django.core.management.base import BaseCommand

from ...tasks import scrape_podcast_pages


class Command(BaseCommand):
    def handle(self, *args, **options):
        scrape_podcast_pages(50)
