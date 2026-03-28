web: gunicorn --pythonpath './django/' clearinghouse.wsgi --worker-class=gthread --threads=2
release: python django/manage.py migrate && python django/manage.py collectstatic --noinput