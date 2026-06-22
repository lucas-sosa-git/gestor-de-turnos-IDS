FROM python:3.11-slim

# Evita generar archivos __pycache__ dentro del contenedor
ENV PYTHONDONTWRITEBYTECODE=1

# Hace que los logs de Python salgan directo en Docker
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5000

CMD ["python", "app_back.py"]
