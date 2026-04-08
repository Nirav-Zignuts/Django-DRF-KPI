# Django + DRF Advanced API (Boilerplate)

A modular REST API using **Django** and **Django REST Framework** with JWT auth, role-based access, **Products** and **Orders**, filtering/search/pagination, ORM optimizations, optional Redis caching, OpenAPI docs, and minimal API tests.

## Features

- **Authentication:** JWT via [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt)
- **Roles:** `admin`, `manager`, `user` on a custom user model
- **Resources:** Products and orders (with line items)
- **API:** Versioned under `/api/v1/`; filtering (`django-filter`), search, ordering, page size 10
- **Performance:** `select_related` / `prefetch_related` on order queries; short-lived cache for product list (invalidated on product changes)
- **Docs:** Swagger UI from [drf-spectacular](https://drf-spectacular.readthedocs.io/)

## Requirements

- Python 3.11+ (3.12 recommended)
- Optional: **Redis** if you enable Redis caching (see below)

## Quick start

### 1. Clone and virtual environment

```bash
cd "/path/to/Django Task"
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables (optional)

Create a `.env` file in the project root (same folder as `manage.py`) or export variables in your shell.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | dev fallback | **Set a strong value in production** |
| `DJANGO_DEBUG` | `true` | Set `false` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `JWT_ACCESS_MINUTES` | `60` | Access token lifetime |
| `JWT_REFRESH_DAYS` | `7` | Refresh token lifetime |
| `USE_REDIS_CACHE` | `false` | Set `true` to use Redis |
| `REDIS_URL` | `redis://127.0.0.1:6379/1` | Redis connection URL |

### 3. Database migrations

```bash
python manage.py migrate
```

### 4. Seed demo data

Creates three users, sample products, and a demo order for the `user` account:

```bash
python manage.py seed_demo
```

**Demo accounts** (local testing only — change or remove in production):

| Username | Password   | Role    |
|----------|------------|---------|
| `admin`  | `Admin123!`   | admin   |
| `manager`| `Manager123!` | manager |
| `user`   | `User123!`    | user    |

### 5. Run the development server

```bash
python manage.py runserver
```

- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **OpenAPI schema (JSON):** http://127.0.0.1:8000/api/schema/
- **Django admin:** http://127.0.0.1:8000/admin/ (use `admin` after `seed_demo`)

## API overview

Base path: **`/api/v1/`**

### Auth

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/auth/token/` | Body: `username`, `password` → `access`, `refresh` |
| POST | `/api/v1/auth/token/refresh/` | Body: `refresh` → new `access` |
| POST | `/api/v1/auth/register/` | Public registration (creates `user` role) |
| GET | `/api/v1/auth/me/` | Current user (requires `Authorization: Bearer <access>`) |

### Shop

| Resource | Path | Notes |
|----------|------|--------|
| Products | `/api/v1/products/` | List/retrieve: any authenticated user. Create/update/delete: manager or admin |
| Orders | `/api/v1/orders/` | Users see only their orders; managers/admins see all. Status updates: manager/admin. Delete order: admin only |
| Order summary | `/api/v1/orders/{id}/summary/` | Totals using prefetched line items |

Send JWT on protected routes:

```http
Authorization: Bearer <your_access_token>
```

### Role behavior (summary)

- **user:** Browse products; create orders; list/retrieve only **own** orders; stock is decremented when they place an order.
- **manager:** Sees **all** orders (same queryset as admin for listing); can manage products and update order status; order create does not decrement stock (oversell allowed for staff roles per serializer logic).
- **admin:** Same order visibility as manager; **only admin** may delete orders; superuser/staff for Django admin if configured via `seed_demo`.

Use **Swagger** → **Authorize** with `Bearer <token>` to try endpoints interactively.

## Optional: Redis caching

1. Start Redis locally (e.g. default port `6379`).
2. Run with caching enabled:

```bash
USE_REDIS_CACHE=true REDIS_URL=redis://127.0.0.1:6379/1 python manage.py runserver
```

If `USE_REDIS_CACHE` is false, Django uses in-memory (`LocMem`) cache instead.

## Testing

Run the full test suite:

```bash
python manage.py test
```

Tests live in `shop/tests.py` and cover JWT issuance, product list auth, role-based product creation, order creation with stock updates, and order list scoping for regular users.

## Project layout

```
config/          # settings, urls, exception handler
accounts/        # User model, roles, auth views, permissions
shop/            # Product, Order, OrderItem, viewsets, serializers, filters, signals
manage.py
requirements.txt
```

## Production notes

- Set `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, and appropriate `DJANGO_ALLOWED_HOSTS`.
- Use a production database (e.g. PostgreSQL) instead of SQLite.
- Serve behind a reverse proxy (e.g. nginx) with HTTPS.
- Do not rely on `seed_demo` passwords in production.

## License

Use and adapt internally as needed for your organization.
