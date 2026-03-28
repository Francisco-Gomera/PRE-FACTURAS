from waitress import serve

from prefacturas.wsgi import application
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler


app = application
if settings.DEBUG:
    app = StaticFilesHandler(application)

serve(app, host="0.0.0.0", port=8000)


