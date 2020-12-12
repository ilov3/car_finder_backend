# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
import os
import logging

__all__ = ('celery_app',)

LOG_FORMAT = '%(asctime)s::%(levelname)s::%(name)s::%(funcName)s::%(lineno)d:  %(message)s'
LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.INFO)


def setup_logging():
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    logging.getLogger('scrapy').setLevel(LOG_LEVEL)


setup_logging()
