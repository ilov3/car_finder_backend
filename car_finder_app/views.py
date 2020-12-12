from datetime import datetime

import pytz
from rest_framework import viewsets
from django_filters import rest_framework as filters
from rest_framework.decorators import api_view
from rest_framework.response import Response

from car_finder_app.filters import CarSaleFilter
from car_finder_app.models import CarSaleInfo
from car_finder_app.models import SpiderRun
from car_finder_app.serializers import CarSaleSerializer


class CarSaleViewSet(viewsets.ModelViewSet):
    queryset = CarSaleInfo.objects.all()
    serializer_class = CarSaleSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CarSaleFilter


@api_view(['POST'])
def spider_finished(request):
    now = datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)
    try:
        spider_run = SpiderRun.objects.last()
        spider_run.duration = now - spider_run.date
        spider_run.save()
        return Response()
    except SpiderRun.DoesNotExist:
        return Response(status=404)
