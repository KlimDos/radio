from flask import Flask, render_template, url_for

app = Flask(__name__)

app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'secret-key'


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run()
