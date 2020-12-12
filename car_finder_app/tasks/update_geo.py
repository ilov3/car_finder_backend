# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging

from celery import shared_task
from django.contrib.gis.geos import Point
from django.db import transaction

from car_finder_app.models import City
from car_finder_app.util import get_country_code, get_city_coord

logger = logging.getLogger(__name__)


@shared_task
def update_geo():
    for city in City.objects.filter(point=None):
        with transaction.atomic():
            if not city.country.code:
                city.country.code = get_country_code(city.country.name)
                city.country.save()
            country_code = city.country.code
            try:
                city.lat, city.lon = get_city_coord(city.name, country_code)
                city.point = Point(float(city.lon), float(city.lat), srid=4326)
                city.save()
            except TypeError:
                pass
