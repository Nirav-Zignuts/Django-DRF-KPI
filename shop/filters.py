import django_filters

from .models import Order, Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ("is_active", "min_price", "max_price")


class OrderFilter(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ("status", "user")
