/** Индексы MENU_ROWS в radio.js: 0 close, 1 radio, 2 volume, … */
const MENU_ROW_RADIO = 1;
const MENU_ROW_VOLUME = 2;

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
    if (pos === MENU_ROW_VOLUME) {
      event.preventDefault();
      adjustVolume(-1);
    }
    return;
  }
  if (event.key === "]") {
    if (pos === MENU_ROW_VOLUME) {
      event.preventDefault();
      adjustVolume(1);
    }
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    if (pos === MENU_ROW_RADIO && typeof change_text === "function") {
      change_text();
    } else if (pos === MENU_ROW_VOLUME) {
      adjustVolume(-1);
    } else if (typeof stepCarousel === "function") {
      stepCarousel(-1);
    }
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    if (pos === MENU_ROW_RADIO && typeof change_text === "function") {
      change_text();
    } else if (pos === MENU_ROW_VOLUME) {
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
