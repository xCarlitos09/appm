FROM python:3.10-slim

# Instalar dependencias del sistema para Flet
RUN apt-get update && apt-get install -y \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# El puerto que Railway nos da
EXPOSE 8080

# Comando para ejecutar la app en modo web
CMD ["flet", "run", "--web", "--port", "8080", "appm.py"]