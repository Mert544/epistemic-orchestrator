from __future__ import annotations

from pathlib import Path


def create_django_mini_examples(base: Path) -> None:
    """Create a synthetic Django project with deliberate issues.

    Used by test_real_world_validation to prove Apex detects real issues.
    Issues:
    - raw SQL injection in views.py (cursor.execute with f-string)
    - missing CSRF on sensitive view (settings.py has csrf off)
    - hardcoded secret key
    - missing type annotations
    - bare except
    - no tests for core module
    """
    root = base / "django_mini"
    root.mkdir(parents=True, exist_ok=True)

    # settings.py
    (root / "settings.py").write_text(
        '''SECRET_KEY = "django-insecure-hardcoded-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",  # disabled!
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
''',
        encoding="utf-8",
    )

    # views.py
    (root / "views.py").write_text(
        '''from django.http import JsonResponse
from django.db import connection
import json

def user_detail(request, user_id):
    # Issue: SQL injection via f-string
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM auth_user WHERE id = {user_id}")
        row = cursor.fetchone()
    return JsonResponse({"user": row})

def process_payment(request):
    try:
        data = json.loads(request.body)
        amount = data["amount"]
        # Issue: no validation
        return JsonResponse({"status": "charged", "amount": amount})
    except:
        # Issue: bare except
        return JsonResponse({"error": "failed"}, status=500)

def admin_override(request):
    # Issue: no auth check
    return JsonResponse({"admin": True})
''',
        encoding="utf-8",
    )

    # models.py
    (root / "models.py").write_text(
        '''from django.db import models

class Order(models.Model):
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)

    def process(self):
        # Issue: no docstring, no type hints
        if self.status == "pending":
            self.status = "completed"
            self.save()
''',
        encoding="utf-8",
    )

    # urls.py
    (root / "urls.py").write_text(
        '''from django.urls import path
from . import views

urlpatterns = [
    path("user/<int:user_id>/", views.user_detail),
    path("payment/", views.process_payment),
    path("admin/override/", views.admin_override),
]
''',
        encoding="utf-8",
    )

    # No tests directory → untested module

    # __init__.py
    (root / "__init__.py").write_text("", encoding="utf-8")
