# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import json
import logging
from time import time, sleep
import multiprocessing as mp

import redis
from datetime import timedelta
from django.conf import settings
import django

django.setup()
from car_finder_app.models import *
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from car_finder.spiders.Drive2 import Drive2Spider

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


def iterate_through_key(key, retrieve_size=100):
    r = redis.Redis(host=settings.SCRAPY_REDIS_HOST, port=settings.SCRAPY_REDIS_PORT)
    i = 0
    while True:
        chunk = r.lrange(key, i * retrieve_size, i * retrieve_size + retrieve_size - 1)
        if not chunk:
            break
        yield chunk
        i += 1


def push_new_sale_to_redis(*car_sale_infos):
    r = redis.Redis(host=settings.SCRAPY_REDIS_HOST, port=settings.SCRAPY_REDIS_PORT)
    for chat_id in r.hkeys('telegram_chat_ids'):
        for car_sale_info in car_sale_infos:
            r.lpush(chat_id, f'{car_sale_info}')


def load_into_db():
    print('Starting to load sale infos into DB..')
    start = time()
    spider_run = SpiderRun.objects.last()
    CarSaleInfo.objects.all().update(is_new=False)
    new_sale_infos = []
    for items in iterate_through_key(settings.SCRAPY_ITEMS_REDIS_KEY):
        for item in items:
            item = json.loads(item)
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
                print(f'New {car_sale} added')
                new_sale_infos.append(car_sale)

    push_new_sale_to_redis(*new_sale_infos)
    r = redis.Redis(host=settings.SCRAPY_REDIS_HOST, port=settings.SCRAPY_REDIS_PORT)
    r.delete(settings.SCRAPY_ITEMS_REDIS_KEY)
    print(f'{len(new_sale_infos)} new car sale info added. Took {time()-start}s')


def start_crawl():
    start = time()
    spider_run = SpiderRun()
    process = CrawlerProcess(get_project_settings())
    process.crawl(Drive2Spider)
    process.start()
    spider_run.duration = timedelta(seconds=time() - start)
    spider_run.save()


if __name__ == '__main__':
    while True:
        try:
            p1 = mp.Process(target=start_crawl)
            p1.start()
            p1.join()
            p1 = mp.Process(target=load_into_db)
            p1.start()
            p1.join()
            sleep(60 * 5)
        except Exception as e:
            logger.exception(e)
