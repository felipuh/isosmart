from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    """Tarea simple de suma"""
    result = x + y
    logger.info(f"Suma: {x} + {y} = {result}")
    return result

@shared_task
def test_task():
    """Tarea de prueba"""
    logger.info("✓ Tarea de prueba ejecutada")
    return "OK"
