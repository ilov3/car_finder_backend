# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging
from time import sleep

import redis
import django

django.setup()
from car_finder_app.models import CarBrand, Country

__author__ = 'ilov3'
logger = logging.getLogger(__name__)

BRANDS_KEY = 'brands'
MODELS_KEY_PATTERN = '{brand}:models'
COUNTRIES_KEY = 'countries'
CITIES_KEY_PATTERN = '{country}:cities'

R = redis.Redis()


def sync_redis_entities():
    logger.info('Sync redis entities')
    for brand in CarBrand.objects.all():
        R.hset(BRANDS_KEY, brand.id, brand.name)
        for model in brand.car_models.all():
            R.hset(MODELS_KEY_PATTERN.format(brand=brand.id), model.id, model.name)
    for country in Country.objects.all():
        R.hset(COUNTRIES_KEY, country.id, country.name)
        for city in country.cities.all():
            R.hset(CITIES_KEY_PATTERN.format(country=country.id), city.id, city.name)
    logger.info('Sync finished')


if __name__ == '__main__':
    while True:
        try:
            sync_redis_entities()
            sleep(60 * 60 * 12)
        except Exception as e:
            logger.error(f'Error occurred: {e}')
