from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def test_task():
    """Tarea de prueba para verificar Celery"""
    logger.info("✓ Tarea de prueba ejecutada correctamente")
    return "Celery funciona correctamente"

@shared_task
def add(x, y):
    """Tarea simple de suma"""
    return x + y
