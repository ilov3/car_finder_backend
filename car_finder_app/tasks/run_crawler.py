# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging

import requests
from celery import shared_task
from django.conf import settings

from car_finder_app.models import SpiderRun

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


@shared_task
def car_finder_crawl():
    spider_run = SpiderRun.objects.create()
    url = f'http://{settings.SCRAPYD_HOST}:{settings.SCRAPYD_PORT}/schedule.json'
    try:
        response = requests.post(url, data={'project': 'car_finder', 'spider': 'Drive2'})
        assert response.status_code == 200, f'Failed to start spider: {response.status_code}::{response.text}'
    except (AssertionError, ConnectionError) as e:
        logger.error(f'Failed to start spider: {e}')
        spider_run.delete()
