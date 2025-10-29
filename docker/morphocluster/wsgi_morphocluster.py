# /code/wsgi_morphocluster.py
from werkzeug.middleware.proxy_fix import ProxyFix
from morphocluster import create_app

class PrefixMiddleware:
    """
    Sets SCRIPT_NAME so Flask knows it's deployed at /morphocluster.
    This makes url_for() and redirects include the prefix.
    Apache forwards WITH the prefix, and this middleware tells Flask about it.
    """
    def __init__(self, app, prefix='/morphocluster'):
        self.app = app
        self.prefix = prefix.rstrip('/')

    def __call__(self, environ, start_response):
        # Set SCRIPT_NAME for Flask's URL generation
        environ['SCRIPT_NAME'] = self.prefix
        # PATH_INFO comes from Apache with the prefix, so strip it
        path_info = environ.get('PATH_INFO', '')
        if path_info.startswith(self.prefix):
            environ['PATH_INFO'] = path_info[len(self.prefix):] or '/'
        return self.app(environ, start_response)

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_port=1)
app.wsgi_app = PrefixMiddleware(app.wsgi_app, '/morphocluster')

