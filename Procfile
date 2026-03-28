web: gunicorn --pythonpath './django/' clearinghouse.wsgi
release: python django/manage.py migrate && python django/manage.py collectstatic --noinput