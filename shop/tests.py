from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from shop.models import Order, Product


class ShopAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="t_admin",
            password="pass12345",
            role=Role.ADMIN,
        )
        cls.manager = User.objects.create_user(
            username="t_manager",
            password="pass12345",
            role=Role.MANAGER,
        )
        cls.user = User.objects.create_user(
            username="t_user",
            password="pass12345",
            role=Role.USER,
        )
        cls.product = Product.objects.create(
            name="Test SKU",
            slug="test-sku",
            description="x",
            price=Decimal("10.00"),
            stock=5,
        )

    def _token(self, username, password="pass12345"):
        url = reverse("token_obtain_pair")
        r = self.client.post(url, {"username": username, "password": password}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        return r.data["access"]

    def test_jwt_obtain(self):
        url = reverse("token_obtain_pair")
        r = self.client.post(
            url, {"username": "t_user", "password": "pass12345"}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_product_list_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token('t_user')}")
        url = reverse("product-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(r.data.get("count", 0), 1)

    def test_product_create_denied_for_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token('t_user')}")
        url = reverse("product-list")
        r = self.client.post(
            url,
            {
                "name": "Nope",
                "slug": "nope",
                "description": "",
                "price": "1.00",
                "stock": 1,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_create_allowed_for_manager(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token('t_manager')}")
        url = reverse("product-list")
        r = self.client.post(
            url,
            {
                "name": "New Item",
                "slug": "new-item",
                "description": "d",
                "price": "2.50",
                "stock": 3,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_order_create_decrements_stock_for_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token('t_user')}")
        url = reverse("order-list")
        r = self.client.post(
            url,
            {
                "notes": "hi",
                "items": [{"product_id": self.product.id, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_user_sees_only_own_orders(self):
        Order.objects.create(user=self.admin, notes="other")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token('t_user')}")
        url = reverse("order-list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        for row in r.data.get("results", r.data if isinstance(r.data, list) else []):
            self.assertEqual(row["user"], self.user.id)
