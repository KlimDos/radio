document
  .getElementById("body")
  .addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown") {
      //console.log("ArrowDown");
      //document.getElementById("result").innerHTML = `ArrowDown`;
      showSelect(1)
    }
  });

document
  .getElementById("body")
  .addEventListener("keydown", function (event) {
    if (event.key === "ArrowUp") {
      //console.log("ArrowUp");
      //document.getElementById("result").innerHTML = `ArrowUp`;
      showSelect(-1)
    }
  });

window.onload = function () {
  document.getElementById("body").focus();
};
