import time

from fastapi import Request

from app.services.metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency = time.perf_counter() - start
    route = request.url.path
    REQUEST_COUNT.labels(route=route, method=request.method, status=response.status_code).inc()
    REQUEST_LATENCY.labels(route=route, method=request.method).observe(latency)
    if response.status_code >= 400:
        ERROR_COUNT.labels(route=route, method=request.method, status=response.status_code).inc()
    return response
