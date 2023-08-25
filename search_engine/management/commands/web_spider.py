from time import sleep
import logging
from django.core.management.base import BaseCommand
from search_engine.crawlers import web_weave

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument('--name', type=int)
        ...

    def handle(self, *args, **options):
        LOGGER.info('Starting Web Spider')
        while True:
            try:
                web_weave()
            except Exception as e:
                LOGGER.error(str(e))
            sleep(60)

