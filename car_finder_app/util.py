# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging
import os
import geocoder

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


def get_country_code(country_name):
    try:
        g = geocoder.geonames(country_name, key=os.environ.get('GEO_TOKEN', 'ilov3'))
        return g.geojson['features'][0]['properties']['country_code']
    except Exception as e:
        logger.error(f'Can not find code for country: {country_name}. Error: {e}')


def get_city_coord(city_name, country_code):
    try:
        g = geocoder.geonames(city_name, country=[country_code], key=os.environ.get('GEO_TOKEN', 'ilov3'))
        logger.debug(f'Found coords: {g.latlng} for {city_name}')
        return g.latlng
    except Exception as e:
        logger.error(f'Can not find coordinate for city: {city_name}. Error: {e}')
        return None, None
