import logging
import time


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("real_estate.requests")

    def __call__(self, request):
        start_time = time.perf_counter()
        self.logger.info("Incoming %s %s", request.method, request.path)

        try:
            response = self.get_response(request)
        except Exception:
            self.logger.exception("Unhandled exception for %s %s", request.method, request.path)
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.logger.info(
            "Completed %s %s with status %s in %.2fms",
            request.method,
            request.path,
            getattr(response, "status_code", None),
            duration_ms,
        )
        return response