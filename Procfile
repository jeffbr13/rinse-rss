web: cd rinse_rss; python manage.py collectstatic --noinput; python manage.py migrate --noinput; waitress-serve --port=$PORT rinse_rss.wsgi:application
worker: python -u rinse_rss/manage.py run_huey
