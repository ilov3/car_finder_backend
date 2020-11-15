from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.gis.db.models.functions import Distance
from django.contrib.humanize.templatetags.humanize import naturaltime, intcomma
from django.db.models import Q

from car_finder_app.models import CarSaleInfo, CarModel, CarBrand, Generation, SpiderRun, UserProfile, City


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SharedState(object):
    __metaclass__ = Singleton
    state = {}


class PriceFilter(admin.SimpleListFilter):
    title = 'Price'

    parameter_name = 'price'

    def lookups(self, request, model_admin):
        return (
            ('to300', 'to 300,000'),
            ('to500', '300,000 to 500,000'),
            ('to700', '500,000 to 700,000'),
            ('to1000', '700,000 to 1.000,000'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'to300':
            return queryset.filter(price__lte=300000)
        if self.value() == 'to500':
            return queryset.filter(price__lte=500000, price__gt=300000)
        if self.value() == 'to700':
            return queryset.filter(price__lte=700000, price__gt=500000)
        if self.value() == 'to1000':
            return queryset.filter(price__lte=1000000, price__gt=700000)


class InSaleFilter(admin.SimpleListFilter):
    title = 'Status'

    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('sold', 'Sold'),
            ('insale', 'In sale'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'sold':
            last_spider_run = SpiderRun.objects.last()
            return queryset.filter(~Q(last_spider_run=last_spider_run))
        if self.value() == 'insale':
            last_spider_run = SpiderRun.objects.last()
            return queryset.filter(last_spider_run=last_spider_run)


class DistanceFilter(admin.SimpleListFilter):
    title = 'Distance range'
    parameter_name = 'distance'

    def lookups(self, request, model_admin):
        return (
            ('50km', '50 Km'),
            ('100km', '100 Km'),
            ('200km', '200 Km'),
            ('300km', '300 Km'),
            ('500km', '500 Km'),
            ('900km', '900 Km'),
        )

    def queryset(self, request, queryset):
        user = request.user
        distance = None
        if user.profile and user.profile.city:
            city = user.profile.city
            if self.value() == '50km':
                distance = (city.point, 50000)
            if self.value() == '100km':
                distance = (city.point, 100000)
            if self.value() == '200km':
                distance = (city.point, 200000)
            if self.value() == '300km':
                distance = (city.point, 300000)
            if self.value() == '500km':
                distance = (city.point, 500000)
            if self.value() == '900km':
                distance = (city.point, 900000)
        if distance:
            queryset = queryset.select_related('city').filter(city__point__distance_lte=distance)
        return queryset


class BrandFilter(AutocompleteFilter):
    field_name = 'brand'
    title = 'car brand'

    def value(self):
        value = super(BrandFilter, self).value()
        state = SharedState()
        state.state[self.field_name] = value
        return value


class ModelFilter(AutocompleteFilter):
    field_name = 'model'
    title = 'car model'

    def value(self):
        value = super(ModelFilter, self).value()
        state = SharedState()
        state.state[self.field_name] = value
        return value


class GenerationFilter(AutocompleteFilter):
    field_name = 'generation'
    title = 'model generation'


@admin.register(CarModel)
class ModelAdmin(admin.ModelAdmin):
    search_fields = ['name']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        state = SharedState()
        if 'brand' in state.state and state.state['brand']:
            queryset = queryset.filter(brand__id=state.state['brand'])
        return queryset, use_distinct


@admin.register(Generation)
class ModelAdmin(admin.ModelAdmin):
    search_fields = ['name']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        state = SharedState()
        if 'brand' in state.state and state.state['brand']:
            queryset = queryset.filter(car_model__brand__id=state.state['brand'])
        if 'model' in state.state and state.state['model']:
            queryset = queryset.filter(car_model__id=state.state['model'])
        return queryset, use_distinct


@admin.register(CarBrand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ['name']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(CarSaleInfo)
class CarSale(admin.ModelAdmin):
    list_display = ('get_country',
                    'get_city',
                    'distance',
                    'model',
                    'get_generation',
                    'manufactured',
                    'purchased',
                    'formatted_price',
                    'url_link',
                    'human_date_added')
    list_display_links = ('human_date_added',)
    autocomplete_fields = ['model', 'brand']
    list_filter = (PriceFilter,
                   InSaleFilter,
                   DistanceFilter,
                   BrandFilter,
                   ModelFilter,
                   GenerationFilter,
                   'date_added',)

    class Media:
        pass

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.profile and user.profile.city:
            user_city = user.profile.city
            qs = qs.select_related('city', 'country', 'model', 'generation').annotate(distance=Distance('city__point', user_city.point))
        return qs

    def distance(self, obj):
        if obj.distance is not None:
            return f'{int(obj.distance.km)} km'

    distance.admin_order_field = 'distance'

    def formatted_price(self, obj):
        if obj.price:
            return intcomma(obj.price)

    formatted_price.short_description = 'Price'
    formatted_price.admin_order_field = 'price'

    def get_city(self, obj):
        return obj.city.name

    get_city.short_description = 'City'
    get_city.admin_order_field = 'city__name'

    def get_country(self, obj):
        return obj.country.name

    get_country.short_description = 'Country'
    get_country.admin_order_field = 'country__name'

    def get_generation(self, obj):
        if obj.generation:
            return obj.generation.name

    get_generation.short_description = 'Generation'
    get_generation.admin_order_field = 'generation__name'

    def human_date_added(self, obj):
        return naturaltime(obj.date_added)

    human_date_added.short_description = 'Date added'
    human_date_added.admin_order_field = 'date_added'
