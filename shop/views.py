import hashlib
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Role
from accounts.permissions import IsAdmin, IsManagerOrAdmin

from .filters import OrderFilter, ProductFilter
from .models import Order, OrderItem, Product
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    ProductSerializer,
)


def _product_list_cache_version():
    v = cache.get("products_list_version")
    if v is None:
        cache.set("products_list_version", 1, timeout=None)
        return 1
    return int(v)


class ProductViewSet(viewsets.ModelViewSet):
    """
    List/detail are cached briefly for identical query strings (see cache version bump on writes).
    Queryset uses select_related only where applicable (Product has no FKs on list).
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ("name", "description", "slug")
    ordering_fields = ("price", "created_at", "name", "stock")
    ordering = ("-created_at",)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrAdmin()]

    def list(self, request, *args, **kwargs):
        ver = _product_list_cache_version()
        q = request.GET.urlencode()
        digest = hashlib.sha256(q.encode()).hexdigest()[:32]
        cache_key = f"products:list:v{ver}:{digest}"
        hit = cache.get(cache_key)
        if hit is not None:
            return Response(hit)
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            cache.set(cache_key, response.data, timeout=60)
        return response

    def get_queryset(self):
        return Product.objects.all()


class OrderViewSet(viewsets.ModelViewSet):
    filterset_class = OrderFilter
    ordering_fields = ("created_at", "status", "id")
    ordering = ("-created_at",)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("partial_update", "update"):
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        base = Order.objects.select_related("user").prefetch_related(
            Prefetch(
                "items",
                queryset=OrderItem.objects.select_related("product"),
            )
        )
        user = self.request.user
        if getattr(user, "role", None) in (Role.ADMIN, Role.MANAGER):
            return base
        return base.filter(user=user)

    @extend_schema(request=OrderCreateSerializer, responses={201: OrderSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read = OrderSerializer(order, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=OrderStatusUpdateSerializer, responses={200: OrderSerializer})
    def partial_update(self, request, *args, **kwargs):
        return self._status_update(request, partial=True)

    def update(self, request, *args, **kwargs):
        return self._status_update(request, partial=False)

    def _status_update(self, request, partial):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read = OrderSerializer(instance, context={"request": request})
        return Response(read.data)

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        """Uses prefetched items when present to compute a line-total without extra queries."""
        order = self.get_object()
        data = OrderSerializer(order, context={"request": request}).data
        total = sum(
            (i.quantity * i.unit_price for i in order.items.all()),
            Decimal("0"),
        )
        data["computed_total"] = str(total.quantize(Decimal("0.01")))
        return Response(data)
