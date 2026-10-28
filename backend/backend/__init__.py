import os
import sys


def _dedupe_syspath_by_realpath() -> None:
	unique_paths = []
	seen = set()
	for path in sys.path:
		key = os.path.realpath(path) if path else path
		if key in seen:
			continue
		seen.add(key)
		unique_paths.append(path)
	sys.path[:] = unique_paths


_dedupe_syspath_by_realpath()

# Esto asegura que Celery se cargue cuando Django inicie
from .celery import app as celery_app

__all__ = ('celery_app',)
