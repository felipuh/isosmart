FROM python:3.12.7-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
RUN groupadd --system isosmart && useradd --system --gid isosmart isosmart
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/ /app/backend/
RUN python manage.py collectstatic --noinput
RUN chmod -R a+rX /app/backend \
 && mkdir -p logs/ai \
 && chown -R isosmart:isosmart logs staticfiles
USER isosmart
EXPOSE 8000
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
