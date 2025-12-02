#!/bin/sh
# Salir inmediatamente si un comando falla
set -e 

# Esperar unos segundos para que la DB se inicialice
# (Opcional, pero previene fallos al inicio)
echo "Esperando a que la base de datos esté lista..."
sleep 5

# Cambiar al directorio donde está manage.py
cd /app/prjLiherfashion/

# 1. Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# 2. Recolectar archivos estáticos
echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

# 3. Arrancar el servidor Gunicorn (Reemplaza el proceso del script)
echo "Iniciando Gunicorn..."
exec gunicorn prjLiherfashion.wsgi:application --bind 0.0.0.0:8000
