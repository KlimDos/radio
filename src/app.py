from flask import Flask, Response, render_template, render_template_string, url_for
import logging
import os
import requests

app = Flask(__name__)


@app.route("/")
def home():
    track_event(
        category='root',
        action='main hit')
    return render_template("index.html")


@app.route("/login")
def login():
    track_event(
        category='login',
        action='main hit')
    return render_template("login.html")


@app.route("/radio")
def radio():
    track_event(
        category='root',
        action='main hit')
    return render_template("radio.html")



# Environment variables are defined in app.yaml.
GA_TRACKING_ID = os.environ['GA_TRACKING_ID']


def track_event(category, action, label=None, value=0):
    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': '555',
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
        'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
    }

    response = requests.post(
        'https://www.google-analytics.com/collect', data=data)

    # If the request fails, this will raise a RequestException. Depending
    # on your application's needs, this may be a non-error and can be caught
    # by the caller.
    response.raise_for_status()

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run()
