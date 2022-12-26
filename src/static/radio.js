function sound(item, song_path) {
  if (item === "Play") {
    console.log(item, song_path);
    // reload after audio
    // audio.onended = function () {
    //   window.location.href = "/delete/" + item;
    // };

    // Play sound effect before start original track
    radio_fx = document.createElement('audio')
    radio_fx.src = 'static/radio-fx.ogg'
// audio.play();
//     createAudio("static/radio-fx.ogg");
    // Pick random timestamp
    timestamp_fx = getRndInteger(0, 24);
    console.log(timestamp_fx);
    radio_fx.currentTime = timestamp_fx;
    radio_fx.play();

    // Stop effect in 4 sec
    // Start original track
    setTimeout(function () {
      radio_fx.pause();
      console.log("start orig radio");
      audio = document.createElement('audio')
      audio.src = 'static/grand-theft-auto-gta-vice.ogg'

      //audio = createAudio("src/static/grand-theft-auto-gta-vice.ogg")
      //audio = new Audio(song_path);
      timestamp = getRndInteger(0, 6225);
      console.log(timestamp);
      audio.currentTime = timestamp;
      audio.play();
    }, 3000);
  } else if (item === "Stop") {
    console.log(item);
    audio.pause();
    //audio.currentTime = 0;
  }
}

function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function change_text(song_path) {

  state = document.getElementById("switch").innerHTML
  console.log(state);

  if (state === "on") {
    document.getElementById("switch").innerHTML = "off";
    sound("Stop", song_path)
  } else {
    document.getElementById("switch").innerHTML = "on";
    sound("Play", song_path)
  }


}

function createAudio(url){
  var audio = document.createElement('audio');
  audio.src = url;
  audio.style.display = "none"; //added to fix ios issue
  audio.autoplay = false; //avoid the user has not interacted with your page issue
  audio.onended = function(){
    audio.remove(); //remove after playing to clean the Dom
  };
  document.body.appendChild(audio);
}
