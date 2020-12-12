# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging
from rest_framework import serializers

from car_finder_app.models import CarSaleInfo

logger = logging.getLogger(__name__)


class CarSaleSerializer(serializers.ModelSerializer):
    model = serializers.ReadOnlyField(source='model.name')
    brand = serializers.ReadOnlyField(source='brand.name')
    generation = serializers.ReadOnlyField(source='generation.name')
    price = serializers.ReadOnlyField(source='pretty_price')
    city = serializers.ReadOnlyField(source='city.name')

    class Meta:
        model = CarSaleInfo
        fields = [
            'url',
            'model',
            'brand',
            'price',
            'generation',
            'manufactured',
            'purchased',
            'city',
            'image',
        ]
