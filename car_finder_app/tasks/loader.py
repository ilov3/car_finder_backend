# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import json
from time import time, sleep
import redis
from django.conf import settings
import django

django.setup()
from car_finder_app.models import *

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


def load_into_db():
    check_ts = time()
    spider_run = SpiderRun.objects.last()
    r = redis.Redis(host=settings.SCRAPY_REDIS_HOST, port=settings.SCRAPY_REDIS_PORT)
    wait = 0
    max_wait = 30
    while True:
        sleep(wait)
        check_spider_run = time() - check_ts > 60
        if check_spider_run:
            spider_run = SpiderRun.objects.last()
            check_ts = time()
        item = r.lpop(settings.SCRAPY_ITEMS_REDIS_KEY)
        if item:
            item = json.loads(item)
            wait = 0
        else:
            if wait <= max_wait:
                wait += 1
            continue

        item_price = item.get('price', None)
        try:
            car_sale = CarSaleInfo.objects.get(url_fingerprint=item['url_fingerprint'])
            car_sale.last_spider_run_id = spider_run.id
            if car_sale.new_price and car_sale.new_price == item_price:
                car_sale.price = item_price
                car_sale.new_price = None
            if car_sale.price != item_price:
                car_sale.new_price = item.get('price', None)
            car_sale.save()
            continue
        except CarSaleInfo.DoesNotExist:
            try:
                country, _ = Country.objects.get_or_create(name=item['country'])
                city, _ = City.objects.get_or_create(name=item['city'], country=country)
                car_brand, _ = CarBrand.objects.get_or_create(name=item['brand'])
                car_model, _ = CarModel.objects.get_or_create(name=item['model'], brand=car_brand)
                generation = None
                if item.get('generation', None):
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
                logger.info(f'New {car_sale} added')
                for chat_id in r.hkeys('telegram_chat_ids'):
                    r.lpush(chat_id, f'{car_sale}')
            except Exception as e:
                logger.error(f'Error occurred while handling {item}. Error: {e}')


if __name__ == '__main__':
    load_into_db()
