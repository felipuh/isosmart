from celery import shared_task
import logging
import time

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    """Tarea simple de suma"""
    result = x + y
    logger.info(f"Suma ejecutada: {x} + {y} = {result}")
    return result

@shared_task
def test_task():
    """Tarea de prueba para verificar Celery"""
    logger.info("✓ Tarea de prueba ejecutada correctamente")
    time.sleep(2)  # Simular trabajo
    return "Celery funciona correctamente"

@shared_task
def multiply(x, y):
    """Tarea de multiplicación"""
    result = x * y
    logger.info(f"Multiplicación: {x} * {y} = {result}")
    return result