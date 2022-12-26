from flask import Flask, Response, render_template, render_template_string, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/radio")
def radio():
    return render_template("radio.html")


if __name__ == "__main__":
    app.run()
