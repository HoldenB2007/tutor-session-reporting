from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness check for Railway; also touches the DB so a broken DATABASE_URL surfaces here."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
