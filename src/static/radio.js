function sound(mode, song_path) {
  const radio_fx = document.getElementById("audio1");
  const audio = document.getElementById("audio2");
  const fx_duration = 3
  var switch_state = document.getElementById("switch").innerHTML;

  if (mode === "Play") {
    console.log(mode);
    // Calculate from random positions for fx and original track
    audio.currentTime = Math.floor(Math.random() * audio.duration);
    radio_fx.currentTime = Math.floor(Math.random() * (radio_fx.duration - fx_duration));

    // Play sound effect before starting the original track
    radio_fx.play();

    // Stop effect after <fx_duration> and start original track
    setTimeout(() => {
      // Make sure switch still on
      if(document.getElementById("switch") != null){
        switch_state = document.getElementById("switch").innerHTML;
        if (switch_state === "on") {
          audio.play();
        }
      }
      radio_fx.pause();
    }, 3000);

  } else if (mode === "Stop") {
    console.log(mode);
    radio_fx.pause();
    audio.pause();
  }
}

function change_text(song_path) {
  state = document.getElementById("switch").innerHTML;

  if (state === "on") {
    document.getElementById("switch").innerHTML = "off";
    document.getElementById("switch_mobile").innerHTML = "off";
    sound("Stop", song_path);
  } else {
    document.getElementById("switch").innerHTML = "on";
    document.getElementById("switch_mobile").innerHTML = "on";
    sound("Play", song_path);
  }
}

var cursor_pos = 1;
function showSelect(move) {
  cursor_pos = cursor_pos + move;
  if (cursor_pos > 7) {
    cursor_pos = 0;
  } else if (cursor_pos < 0) {
    cursor_pos = 7;
  }
  const ids = [
    "menu_radio_switch",
    "menu_volume",
    "menu_radio_name",
    "menu_now_playing",
    "menu_radio_logo",
    "menu_author",
    "menu_back",
  ];

  ids.forEach(myFunction);

  function myFunction(item, index, arr) {
    if (index == cursor_pos) {
      document.getElementById(item).classList.add("select_key");
    } else {
      document.getElementById(item).classList.remove("select_key");
    }
  }
}
