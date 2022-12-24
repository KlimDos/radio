from flask import Flask, render_template, url_for, Response, render_template_string

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


@app.route("/ogg")
def streamogg():
    def generate():
        with open("src/radio/sample4.ogg", "rb") as fogg:
            data = fogg.read(1024)
            while data:
                yield data
                data = fogg.read(1024)
    return Response(generate(), mimetype="audio/ogg")


@app.route('/p')
def p():
    return render_template_string('''
<a href="/delete/{{item}}" onclick="sound()">NORMAL LINK</a><br>

<a href="javascript:void(0);" onclick="sound('{{item}}')">JAVASCRIPT LINK</a>

<script>
function sound(item) {
    //alert("SOUND");
    // create audio 
    var audio = new Audio('/ogg');
    // reload after audio 
    audio.onended = function() { window.location.href="/delete/" + item; }
    //audio.onended = function() { window.location.reload(); }
    // play audio
    audio.play();
}
</script>
''', item="SomeValue")

if __name__ == "__main__":
    app.run()
