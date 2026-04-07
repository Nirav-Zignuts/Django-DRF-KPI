from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from accounts.models import Role

from .models import Order, OrderItem, OrderStatus, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "quantity", "unit_price")


class OrderItemWriteSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source="product",
    )

    class Meta:
        model = OrderItem
        fields = ("product_id", "quantity")

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "user_username",
            "status",
            "notes",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "status", "created_at", "updated_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("notes", "items")

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Order must contain at least one line item.")
        return items

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if user.role not in (Role.ADMIN, Role.MANAGER):
            for line in attrs.get("items", []):
                product = line["product"]
                qty = line["quantity"]
                if product.stock < qty:
                    raise serializers.ValidationError(
                        {"items": f"Insufficient stock for '{product.name}' (available {product.stock})."}
                    )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        items_data = validated_data.pop("items")
        order = Order.objects.create(user=user, notes=validated_data.get("notes", ""))

        for line in items_data:
            product = line["product"]
            qty = line["quantity"]
            if user.role not in (Role.ADMIN, Role.MANAGER):
                product.stock -= qty
                product.save(update_fields=("stock",))
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=product.price,
            )
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("status", "notes")

    def validate_status(self, value):
        if value not in dict(OrderStatus.choices):
            raise serializers.ValidationError("Invalid status.")
        return value
