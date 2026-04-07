from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Product


def bump_product_list_cache_version():
    v = cache.get("products_list_version")
    if v is None:
        cache.set("products_list_version", 1, timeout=None)
    else:
        cache.set("products_list_version", int(v) + 1, timeout=None)


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_list_cache(sender, **kwargs):
    bump_product_list_cache_version()
