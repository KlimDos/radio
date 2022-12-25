// add var
var audio = new Audio("static/sample4.ogg");

function sound(item) {
  if (item === "Play") {
    console.log(item);
    // reload after audio
    // audio.onended = function () {
    //   window.location.href = "/delete/" + item;
    // };
    audio.play();
  } else if (item === "Stop") {
    console.log(item);
    audio.pause();
    //audio.currentTime = 0;
  }
}
