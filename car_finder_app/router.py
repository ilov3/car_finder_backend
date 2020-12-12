# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging

from rest_framework.routers import DefaultRouter

from car_finder_app import views

logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'carsale', views.CarSaleViewSet)
