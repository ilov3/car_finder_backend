# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging
from django_filters import rest_framework as filters

from car_finder_app.models import CarSaleInfo

logger = logging.getLogger(__name__)


class CarSaleFilter(filters.FilterSet):
    class Meta:
        model = CarSaleInfo
        fields = {
            'model__name': ['iexact'],
            'city__name': ['iexact'],
            'brand__name': ['iexact'],
            'price': ['gte', 'lte'],
        }
