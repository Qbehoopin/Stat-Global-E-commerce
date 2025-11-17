# Stat-Global-E-commerce
My First E-commerce website for my clothing company 

# create a venv and install Django + DRF + extras
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install Django djangorestframework psycopg2-binary python-dotenv celery redis stripe django-cors-headers

# start a Django project (if not scaffolded yet)
django-admin startproject project_config .

# create initial app directories
python manage.py startapp core
python manage.py startapp products
python manage.py startapp users