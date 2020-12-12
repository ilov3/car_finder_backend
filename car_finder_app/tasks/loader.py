# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import json
import os
from time import time, sleep
import redis
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db import transaction

from car_finder_app.models import *

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


def process_new_item(item, spider_run, r):
    item_price = item.get('price', None)
    try:
        images = item.get('images', None)
        car_sale = CarSaleInfo.objects.get(url_fingerprint=item['url_fingerprint'])
        car_sale.last_spider_run = spider_run
        if images and not car_sale.image:
            with open(os.path.join('/tmp', images[0]['path']), 'rb') as f:
                django_file = File(f)
                car_sale.image.save(os.path.basename(f.name), django_file)
        if car_sale.new_price and car_sale.new_price == item_price:
            car_sale.price = item_price
            car_sale.new_price = None
        if car_sale.price != item_price:
            car_sale.new_price = item.get('price', None)
        car_sale.save()
    except CarSaleInfo.DoesNotExist:
        try:
            country, _ = Country.objects.get_or_create(name=item['country'])
            city, _ = City.objects.get_or_create(name=item['city'], country=country)
            car_brand, _ = CarBrand.objects.get_or_create(name=item['brand'])
            car_model, _ = CarModel.objects.get_or_create(name=item['model'], brand=car_brand)
            generation = item.get('generation', None)
            images = item.get('images', None)
            if generation:
                generation, _ = Generation.objects.get_or_create(name=item['generation'], car_model=car_model)
            car_sale = CarSaleInfo.objects.create(title=item['title'],
                                                  price=item.get('price', None),
                                                  url=item['url'],
                                                  url_fingerprint=item['url_fingerprint'],
                                                  brand=car_brand,
                                                  model=car_model,
                                                  last_spider_run=spider_run,
                                                  generation=generation,
                                                  manufactured=item.get('manufactured', None),
                                                  purchased=item.get('purchased', None),
                                                  city=city,
                                                  country=country)
            if images:
                with open(os.path.join('/tmp', images[0]['path']), 'rb') as f:
                    django_file = File(f)
                    car_sale.image.save(os.path.basename(f.name), django_file)
            logger.info(f'New {car_sale} added')
            for chat_id in r.hkeys('telegram_chat_ids'):
                r.lpush(chat_id, f'{car_sale}')
        except Exception as e:
            logger.error(f'Error occurred while handling {item}. Error: {e}')


@shared_task
def load_into_db():
    logger.info('Waiting for car sales...')
    check_ts = time()
    spider_run = SpiderRun.objects.last()
    r = redis.Redis(host=settings.SCRAPY_REDIS_HOST, port=settings.SCRAPY_REDIS_PORT)
    wait = 0
    max_wait = 30
    batch = []
    counter = 0
    last_batch_process_ts = 0
    while True:
        sleep(wait)
        check_spider_run = time() - check_ts > 60
        if check_spider_run:
            spider_run = SpiderRun.objects.last()
            check_ts = time()
        item = r.lpop(settings.SCRAPY_ITEMS_REDIS_KEY)
        if item and len(batch) < 100:
            item = json.loads(item)
            batch.append(item)
            wait = 0
            continue
        elif len(batch) == 100 or (batch and (time() - last_batch_process_ts > max_wait)):
            with transaction.atomic():
                for item in batch:
                    process_new_item(item, spider_run, r)
            counter += 1
            last_batch_process_ts = time()
            logger.info(f'Processed new batch({counter}) of size {len(batch)}')
            batch = []
        else:
            if wait <= max_wait:
                wait += 1
            continue
