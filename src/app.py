from flask import Flask, render_template, url_for, send_from_directory
import logging, sys
import os
from dotenv import load_dotenv

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] [%(thread)d] %(levelname)s %(name)s - %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


load_dotenv()

print(os.environ.get('ARTEFACT_VERSION'))

build = os.environ.get('ARTEFACT_VERSION')

app = Flask(__name__)


@app.route("/bank")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/")
def radio():
    return render_template("radio.html", build=build)


@app.route("/test")
def test():
    app.logger.error(
'''[test-multiline] line1
line2
line3)
'''
    )
    return "check logs...", 200


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run()
