# Usamos Python 3.11 ligero
FROM python:3.11-slim

# Variables para optimizar Python en Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema (gcc y librerías para mysql/mariadb)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiamos requerimientos e instalamos
COPY requirements.txt .
COPY requerimients2.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requerimients2.txt

# Copiamos el código
COPY app ./app

# Exponemos el puerto
EXPOSE 8001

# Ejecutamos uvicorn escuchando en todas las interfaces (0.0.0.0)
CMD ["uvicorn", "app.principal:aplicacion", "--host", "0.0.0.0", "--port", "8001", "--reload"]