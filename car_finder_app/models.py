from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.utils.html import format_html


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'Country: {self.name}'


class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return f'{self.country.name}: {self.name}'

    class Meta:
        unique_together = ('name', 'country')


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


class CarSaleInfo(models.Model):
    last_spider_run = models.ForeignKey(SpiderRun, on_delete=models.DO_NOTHING, related_name='sales')
    date_added = models.DateTimeField(auto_now_add=True)
    is_new = models.BooleanField(default=True)
    exclude = models.BooleanField(default=False)
    url_fingerprint = models.CharField(max_length=255, unique=True, db_index=True)
    url = models.URLField()
    model = models.ForeignKey(CarModel, on_delete=models.DO_NOTHING, related_name='sales')
    generation = models.ForeignKey(Generation, on_delete=models.DO_NOTHING, related_name='sales', null=True, blank=True)
    brand = models.ForeignKey(CarBrand, on_delete=models.DO_NOTHING, related_name='sales')
    price = models.IntegerField(blank=True, null=True)
    new_price = models.IntegerField(blank=True, null=True)
    manufactured = models.IntegerField(blank=True, null=True)
    purchased = models.IntegerField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, related_name='sales')
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, related_name='sales')

    def __str__(self):
        price = intcomma(self.price) if self.price else ''
        return f'{self.city}: {self.model}: {price} {self.url}'

    def url_link(self):
        return format_html(f'<a href={self.url} target="_blank">Link</a>')

    class Meta:
        ordering = ('date_added',)
