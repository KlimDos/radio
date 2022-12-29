from flask import Flask, render_template, url_for
import logging, sys
import os
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get('ARTEFACT_VERSION'))

build = os.environ.get('ARTEFACT_VERSION')

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/radio")
def radio():
    return render_template("radio.html", build=build)


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run("--build=we")
