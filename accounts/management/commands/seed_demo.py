from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User
from shop.models import Order, OrderItem, OrderStatus, Product


class Command(BaseCommand):
    help = "Create demo users (admin, manager, user) and sample products for local testing."

    @transaction.atomic
    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.role = Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Admin123!")
        admin.save()

        manager, _ = User.objects.get_or_create(
            username="manager",
            defaults={"email": "manager@example.com", "role": Role.MANAGER},
        )
        manager.role = Role.MANAGER
        manager.set_password("Manager123!")
        manager.save()

        user, _ = User.objects.get_or_create(
            username="user",
            defaults={"email": "user@example.com", "role": Role.USER},
        )
        user.role = Role.USER
        user.set_password("User123!")
        user.save()

        products = [
            ("Wireless Mouse", "wireless-mouse", "Ergonomic wireless mouse.", "29.99", 100),
            ("USB-C Hub", "usb-c-hub", "7-in-1 hub.", "49.50", 40),
            ("Mechanical Keyboard", "mechanical-keyboard", "Tactile switches.", "119.00", 15),
        ]
        for name, slug, desc, price, stock in products:
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": desc,
                    "price": price,
                    "stock": stock,
                    "is_active": True,
                },
            )

        if not Order.objects.filter(user=user).exists():
            p1 = Product.objects.get(slug="wireless-mouse")
            order = Order.objects.create(user=user, status=OrderStatus.PENDING, notes="Demo order")
            OrderItem.objects.create(
                order=order,
                product=p1,
                quantity=2,
                unit_price=p1.price,
            )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("  admin   / Admin123!   (role: admin)")
        self.stdout.write("  manager / Manager123! (role: manager)")
        self.stdout.write("  user    / User123!    (role: user)")
        self.stdout.write("Swagger UI: http://127.0.0.1:8000/api/docs/")
