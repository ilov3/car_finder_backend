# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging
from datetime import datetime

import requests
from celery import Celery
from celery.signals import celeryd_init
from django.conf import settings
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .update_geo import update_geo
from .run_crawler import car_finder_crawl
from .loader import load_into_db

__author__ = 'ilov3'

from ..poll import poll

logger = logging.getLogger(__name__)

app = Celery()


@celeryd_init.connect
def start_loader(sender, **kwargs):
    poll_url = f'http://{settings.SCRAPYD_HOST}:{settings.SCRAPYD_PORT}/listprojects.json'
    poll(lambda: 'car_finder' in requests.get(poll_url).json()['projects'])
    load_into_db.apply_async()
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=40,
        period=IntervalSchedule.MINUTES, )

    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name='Parse drive2',
        task='car_finder_app.tasks.run_crawler.car_finder_crawl',
        defaults={'start_time': datetime.utcnow()},
    )
