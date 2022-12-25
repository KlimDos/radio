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


# @app.route("/ogg")
# def streamogg():
#     def generate():
#         with open("/src/radio/sample4.ogg", "rb") as fogg:
#             data = fogg.read(1024)
#             while data:
#                 yield data
#                 data = fogg.read(1024)
#     return Response(generate(), mimetype="audio/ogg")


if __name__ == "__main__":
    app.run(debug=True)
