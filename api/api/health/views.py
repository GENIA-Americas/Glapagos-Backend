from django.http import JsonResponse
from django.views import View

class HealthCheckView(View):
    http_method_names = ["get", "head"]
    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "healthy", "platform": "Glapagos"}, status=200)
