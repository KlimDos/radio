function sound(mode, song_path) {
  const radio_fx = document.getElementById("audio1");
  const audio = document.getElementById("audio2");
  const fx_duration = 3;
  const switch_state = document.getElementById("switch").innerHTML;

  if (mode === "Play") {
    console.log(mode);
    // Calculate random positions for fx and original track
    audio.currentTime = Math.floor(Math.random() * audio.duration);
    radio_fx.currentTime = Math.floor(Math.random() * (radio_fx.duration - fx_duration));

    // Play sound effect before starting the original track
    radio_fx.play();

    // Stop effect after <fx_duration> and start original track
    setTimeout(() => {
      if (document.getElementById("switch") && document.getElementById("switch").innerHTML === "on") {
        audio.play();
      }
      radio_fx.pause();
    }, fx_duration * 1000);

  } else if (mode === "Stop") {
    console.log(mode);
    radio_fx.pause();
    audio.pause();
  }
}

function change_text(song_path) {
  const state = document.getElementById("switch").innerHTML;

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

let cursor_pos = 1;
function showSelect(move) {
  cursor_pos += move;
  if (cursor_pos > 6) {
    cursor_pos = 0;
  } else if (cursor_pos < 0) {
    cursor_pos = 6;
  }
  const ids = [
    "menu_radio_switch",
    "menu_volume",
    // "menu_radio_name",
    "menu_now_playing",
    "menu_radio_logo",
    "menu_author",
    "menu_back",
  ];

  ids.forEach((item, index) => {
    const element = document.getElementById(item);
    if (index === cursor_pos) {
      element.classList.add("select_key");
    } else {
      element.classList.remove("select_key");
    }
  });
}
