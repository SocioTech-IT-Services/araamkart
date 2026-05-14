"""Early-exit middleware for load balancer / Railway probes."""
from django.http import HttpResponse

_HEALTH_PATHS = frozenset({"/_health", "/_health/"})


class HealthCheckMiddleware:
    """Answer health checks before SessionMiddleware (no DB, no session table)."""

    __slots__ = ("get_response",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in _HEALTH_PATHS:
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
