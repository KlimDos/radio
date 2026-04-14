const MENU_ROWS = [
  ["menu_radio_switch", "menu_radio_switch_mobile"],
  ["menu_volume", "menu_volume_mobile"],
  ["menu_now_playing", "menu_now_playing_mobile"],
  ["menu_radio_logo", "menu_radio_logo_mobile"],
  ["menu_clock", "menu_clock_mobile"],
  ["menu_author", "menu_author_mobile"],
];

let volumeLevel = 4;
var cursor_pos = 0;

let audioUnlockDone = false;
let sharedAudioContext = null;

/**
 * Синхронно в том же стеке, что и keydown/click (важно для autoplay):
 * WebAudio resume + короткий muted play/pause на обоих <audio>.
 */
function primeAudioUnlockSync() {
  if (audioUnlockDone) {
    return;
  }
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) {
      sharedAudioContext = sharedAudioContext || new AC();
      if (sharedAudioContext.state === "suspended") {
        sharedAudioContext.resume();
      }
    }
  } catch (e) {
    /* ignore */
  }

  const { radio_fx, audio } = getAudios();
  if (!radio_fx || !audio) {
    return;
  }

  const primeEl = (el) => {
    const prevVol = el.volume;
    const prevMuted = el.muted;
    try {
      el.muted = true;
      el.volume = 0;
      el.play().catch(() => {});
      el.pause();
      el.currentTime = 0;
    } catch (e) {
      /* ignore */
    } finally {
      el.muted = prevMuted;
      el.volume = prevVol;
    }
  };

  primeEl(radio_fx);
  primeEl(audio);
  applyVolumeToAudios();
  audioUnlockDone = true;
}

function getAudios() {
  return {
    radio_fx: document.getElementById("audio1"),
    audio: document.getElementById("audio2"),
  };
}

function applyVolumeToAudios() {
  const v = Math.max(0, Math.min(10, volumeLevel)) / 10;
  const { radio_fx, audio } = getAudios();
  if (radio_fx) radio_fx.volume = v;
  if (audio) audio.volume = v;
}

function updateVolumeDisplay() {
  const n = String(Math.max(0, Math.min(10, volumeLevel)));
  const a = document.getElementById("volume_level");
  const b = document.getElementById("volume_level_mobile");
  if (a) a.textContent = n;
  if (b) b.textContent = n;
}

function adjustVolume(delta) {
  volumeLevel += delta;
  if (volumeLevel > 10) volumeLevel = 10;
  if (volumeLevel < 0) volumeLevel = 0;
  applyVolumeToAudios();
  updateVolumeDisplay();
}

function randomSeekSeconds(el, reserveEnd) {
  if (!el || !isFinite(el.duration) || el.duration <= 0) return;
  const max = el.duration - (reserveEnd || 0);
  if (max <= 0) return;
  el.currentTime = Math.floor(Math.random() * max);
}

function sound(mode) {
  const { radio_fx, audio } = getAudios();
  if (!radio_fx || !audio) return;

  const fx_duration = 3;

  if (mode === "Play") {
    randomSeekSeconds(audio, 1);
    randomSeekSeconds(radio_fx, fx_duration + 0.5);

    radio_fx.play().catch(() => {});

    setTimeout(() => {
      const sw = document.getElementById("switch");
      if (sw && sw.textContent.trim() === "on") {
        audio.play().catch(() => {});
      }
      radio_fx.pause();
    }, fx_duration * 1000);
  } else if (mode === "Stop") {
    radio_fx.pause();
    audio.pause();
  }
}

function change_text() {
  const sw = document.getElementById("switch");
  const swm = document.getElementById("switch_mobile");
  if (!sw) return;

  const state = sw.textContent.trim();

  if (state === "on") {
    sw.textContent = "off";
    if (swm) swm.textContent = "off";
    sound("Stop");
    updateTrackPosition();
    return;
  }

  primeAudioUnlockSync();
  sw.textContent = "on";
  if (swm) swm.textContent = "on";
  sound("Play");
  updateTrackPosition();
}

function applyMenuHighlight() {
  MENU_ROWS.forEach((pair, index) => {
    pair.forEach((id) => {
      const element = document.getElementById(id);
      if (!element) return;
      if (index === cursor_pos) {
        element.classList.add("select_key");
      } else {
        element.classList.remove("select_key");
      }
    });
  });
}

function showSelect(move) {
  cursor_pos += move;
  if (cursor_pos > MENU_ROWS.length - 1) {
    cursor_pos = 0;
  } else if (cursor_pos < 0) {
    cursor_pos = MENU_ROWS.length - 1;
  }
  applyMenuHighlight();
}

function setMenuRow(index) {
  const n = MENU_ROWS.length;
  if (n === 0) return;
  cursor_pos = ((index % n) + n) % n;
  applyMenuHighlight();
}

function wireMenuRowsMouse() {
  MENU_ROWS.forEach((pair, index) => {
    pair.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("mouseenter", function () {
        setMenuRow(index);
      });
    });
  });
}

function menuActivate() {
  if (cursor_pos === 0) {
    change_text();
  } else if (cursor_pos === MENU_ROWS.length - 1) {
    const row =
      document.getElementById("menu_author") || document.getElementById("menu_author_mobile");
    const link = row && row.querySelector("a.vc-repo-link");
    if (link && link.href) {
      window.open(link.href, "_blank", "noopener,noreferrer");
    }
  }
}

const VICE_CITY_TZ = "America/New_York";

function formatViceCityTime(date) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: VICE_CITY_TZ,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

function formatTrackClock(seconds) {
  if (!isFinite(seconds) || seconds < 0) {
    return "--:--";
  }
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function updateVcClock() {
  const now = new Date();
  const s = formatViceCityTime(now);
  const a = document.getElementById("clock_time");
  const b = document.getElementById("clock_time_mobile");
  if (a) a.textContent = s;
  if (b) b.textContent = s;
}

function updateTrackPosition() {
  const audio = document.getElementById("audio2");
  const sw = document.getElementById("switch");
  const a = document.getElementById("track_pos");
  const b = document.getElementById("track_pos_mobile");
  const bar = document.getElementById("track_bar_fill");
  const barM = document.getElementById("track_bar_fill_mobile");
  const radioOff = !sw || sw.textContent.trim() === "off";

  let line = "--:--";
  let pct = 0;
  if (!radioOff && audio) {
    const cur = audio.currentTime;
    line = formatTrackClock(cur);
    if (isFinite(audio.duration) && audio.duration > 0) {
      line += " / " + formatTrackClock(audio.duration);
      pct = Math.min(100, Math.max(0, (100 * cur) / audio.duration));
    }
  }

  if (a) a.textContent = line;
  if (b) b.textContent = line;
  if (bar) bar.style.width = pct + "%";
  if (barM) barM.style.width = pct + "%";
}

function initRadioUi() {
  applyVolumeToAudios();
  updateVolumeDisplay();
  showSelect(0);
  wireMenuRowsMouse();

  updateVcClock();
  setInterval(updateVcClock, 1000);
  updateTrackPosition();

  document.addEventListener(
    "pointerdown",
    function () {
      primeAudioUnlockSync();
    },
    true
  );

  const { radio_fx, audio } = getAudios();
  const reapply = () => {
    applyVolumeToAudios();
  };
  if (radio_fx) {
    radio_fx.addEventListener("loadedmetadata", reapply);
  }
  if (audio) {
    audio.addEventListener("loadedmetadata", reapply);
    audio.addEventListener("loadedmetadata", updateTrackPosition);
    audio.addEventListener("timeupdate", updateTrackPosition);
    audio.addEventListener("play", updateTrackPosition);
    audio.addEventListener("pause", updateTrackPosition);
    audio.addEventListener("seeked", updateTrackPosition);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initRadioUi);
} else {
  initRadioUi();
}

function getMenuCursorPos() {
  return cursor_pos;
}

function stepCarousel(direction) {
  const el = document.getElementById("backgroundCard");
  if (!el || typeof bootstrap === "undefined") {
    return;
  }
  const c =
    bootstrap.Carousel.getInstance(el) || bootstrap.Carousel.getOrCreateInstance(el);
  if (direction < 0) {
    c.prev();
  } else {
    c.next();
  }
}
