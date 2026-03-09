from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
import os


def setup_prometheus(app):
    """
    Configure Prometheus pour FastAPI

    Args:
        app: Instance FastAPI
    """
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    print("✅ Prometheus metrics enabled at /metrics")

# Créer métrique histogram pour latence
inference_time_histogram = Histogram(
    'inference_time_ms',
    'Temps d\'inférence en ms'
)

# Fonction : Track inference time
def track_inference_time(inference_time_ms: float):
    """Enregistre le temps d'inférence"""
    inference_time_histogram.observe(inference_time_ms)