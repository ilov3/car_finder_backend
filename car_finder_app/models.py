import logging
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.gis.db import models
from django.utils.html import format_html

from car_finder_app.util import get_country_code, get_city_coord

__author__ = 'ilov3'
logger = logging.getLogger(__name__)


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return f'Country: {self.name}'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None and self.code is None:
            try:
                self.code = get_country_code(self.name)
            except Exception as e:
                logger.warn(f'Exception: {e}')
        super().save(force_insert, force_update, using, update_fields)


class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    point = models.PointField(srid=4326, null=True, blank=True, geography=True)

    def __str__(self):
        return f'{self.country.name}: {self.name}'

    class Meta:
        unique_together = ('name', 'country')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None and self.lat is None and self.lon is None:
            try:
                country_code = self.country.code
                self.lat, self.lon = get_city_coord(self.name, country_code)
                self.point = Point(self.lon, self.lat, srid=4326)
            except Exception as e:
                logger.warn(f'Exception: {e}')
        super().save(force_insert, force_update, using, update_fields)


class CarBrand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'Brand: {self.name}'


class CarModel(models.Model):
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='car_models')

    def __str__(self):
        return f'{self.brand.name}: {self.name}'

    class Meta:
        unique_together = ('name', 'brand')


class Generation(models.Model):
    name = models.CharField(max_length=255)
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name='generations')

    def __str__(self):
        return f'{self.car_model}: {self.name}'

    class Meta:
        unique_together = ('name', 'car_model')


class SpiderRun(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return f'Car search {self.date}. Duration: {self.duration}'


class Car(models.Model):
    model = models.ForeignKey(CarModel, on_delete=models.DO_NOTHING, related_name='cars')
    generation = models.ForeignKey(Generation, on_delete=models.DO_NOTHING, related_name='cars', null=True, blank=True)
    manufactured = models.IntegerField(blank=True, null=True)
    purchased = models.IntegerField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, related_name='cars')
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, related_name='cars')
    capacity = models.FloatField(null=True, blank=True)
    horse_power = models.SmallIntegerField(null=True, blank=True)
    engine_type = models.CharField(max_length=20)
    gear_type = models.CharField(max_length=20)
    transmission = models.CharField(max_length=20)

    url_fingerprint = models.CharField(max_length=255, unique=True, db_index=True)
    url = models.URLField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_spider_run = models.ForeignKey(SpiderRun, on_delete=models.DO_NOTHING, related_name='cars')

    def __str__(self):
        return f'{self.model} {self.city} {self.title}'


class CarSaleInfo(models.Model):
    last_spider_run = models.ForeignKey(SpiderRun, on_delete=models.DO_NOTHING, related_name='sales')
    date_added = models.DateTimeField(auto_now_add=True)
    is_new = models.BooleanField(default=True)
    exclude = models.BooleanField(default=False)
    url_fingerprint = models.CharField(max_length=255, unique=True, db_index=True)
    url = models.URLField()
    model = models.ForeignKey(CarModel, on_delete=models.DO_NOTHING, related_name='sales')  # to delete
    generation = models.ForeignKey(Generation, on_delete=models.DO_NOTHING, related_name='sales', null=True, blank=True)  # to delete
    brand = models.ForeignKey(CarBrand, on_delete=models.DO_NOTHING, related_name='sales')  # to delete
    price = models.IntegerField(blank=True, null=True)
    new_price = models.IntegerField(blank=True, null=True)
    manufactured = models.IntegerField(blank=True, null=True)  # to delete
    purchased = models.IntegerField(blank=True, null=True)  # to delete
    title = models.TextField(blank=True, null=True)  # to delete
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, related_name='sales')  # to delete
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, related_name='sales')  # to delete
    car = models.ForeignKey(Car, null=True, blank=True, related_name='sales', on_delete=models.DO_NOTHING)

    def __str__(self):
        price = intcomma(self.price) if self.price else ''
        return f'{self.city}: {self.model}: {price} {self.url}'

    def url_link(self):
        return format_html(f'<a href={self.url} target="_blank">Link</a>')

    class Meta:
        ordering = ('-date_added',)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile', null=True, blank=True, on_delete=models.DO_NOTHING)
    city = models.ForeignKey(City, related_name='profiles', null=True, blank=True, on_delete=models.DO_NOTHING)
    telegram_id = models.IntegerField(null=True, blank=True)
