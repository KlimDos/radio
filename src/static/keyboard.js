document
  .getElementById("body")
  .addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown") {
      console.log("ArrowDown");
      document.getElementById("result").innerHTML = `ArrowDown`;
    }
  });

document
  .getElementById("body")
  .addEventListener("keydown", function (event) {
    if (event.key === "ArrowUp") {
      console.log("ArrowUp");
      document.getElementById("result").innerHTML = `ArrowUp`;
    }
  });

window.onload = function () {
  document.getElementById("body").focus();
};
