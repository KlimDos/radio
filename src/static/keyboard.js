function radioKeydownHandler(event) {
  const t = event.target;
  if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) {
    return;
  }

  const pos = typeof getMenuCursorPos === "function" ? getMenuCursorPos() : 0;

  if (typeof primeAudioUnlockSync === "function") {
    primeAudioUnlockSync();
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    showSelect(1);
    return;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    showSelect(-1);
    return;
  }

  if (event.key === "[") {
    if (pos === 1) {
      event.preventDefault();
      adjustVolume(-1);
    }
    return;
  }
  if (event.key === "]") {
    if (pos === 1) {
      event.preventDefault();
      adjustVolume(1);
    }
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    if (pos === 0 && typeof change_text === "function") {
      change_text();
    } else if (pos === 1) {
      adjustVolume(-1);
    } else if (typeof stepCarousel === "function") {
      stepCarousel(-1);
    }
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    if (pos === 0 && typeof change_text === "function") {
      change_text();
    } else if (pos === 1) {
      adjustVolume(1);
    } else if (typeof stepCarousel === "function") {
      stepCarousel(1);
    }
    return;
  }

  if (event.key === "Enter") {
    event.preventDefault();
    if (typeof menuActivate === "function") {
      menuActivate();
    }
  }
}

document.addEventListener("keydown", radioKeydownHandler, true);

window.onload = function () {
  const b = document.getElementById("body");
  if (b) b.focus();
};
