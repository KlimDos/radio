/**
 * WebVTT → cues, sync with <audio id="audio2"> via timeupdate.
 * Optional: data-captions-src on that element for a non-default .vtt (e.g. …-first.vtt while v2 is WIP).
 * Cues are shown only while audio2 is actually playing — during the FX intro audio2 stays paused
 * but currentTime is already set, so we avoid mismatched subtitles over the wrong sound.
 */
(function () {
  const CAPTIONS_ID = "vc-captions";
  let cues = [];
  let audioEl = null;

  function parseVttTimestamp(raw) {
    const s = raw.trim().replace(",", ".");
    const p = s.split(":");
    let h = 0;
    let m = 0;
    let sec = 0;
    if (p.length === 3) {
      const last = p[2];
      // Some exports use HH:MM:SSS with no dot (e.g. 00:02:040 = 2.040s). Plain parseFloat("040") === 40 breaks cues.
      const hasFraction = last.includes(".") || s.includes(".");
      if (!hasFraction && /^\d{3}$/.test(last)) {
        return (parseInt(p[0], 10) || 0) * 60 + (parseInt(p[1], 10) || 0) + (parseInt(last, 10) || 0) / 1000;
      }
      h = parseInt(p[0], 10) || 0;
      m = parseInt(p[1], 10) || 0;
      sec = parseFloat(last) || 0;
    } else if (p.length === 2) {
      m = parseInt(p[0], 10) || 0;
      sec = parseFloat(p[1]) || 0;
    } else {
      sec = parseFloat(s) || 0;
    }
    return h * 3600 + m * 60 + sec;
  }

  function parseVtt(text) {
    const out = [];
    const blocks = text.replace(/^\uFEFF/, "").trim().split(/\n{2,}/);
    for (const block of blocks) {
      const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
      if (!lines.length || lines[0].startsWith("NOTE") || lines[0].startsWith("Kind:") || lines[0].startsWith("Language:")) {
        continue;
      }
      if (lines[0] === "WEBVTT") {
        continue;
      }
      let i = 0;
      if (lines[0].includes("-->")) {
        i = 0;
      } else if (lines.length > 1 && lines[1].includes("-->")) {
        i = 1;
      } else {
        continue;
      }
      const timeLine = lines[i];
      const arrow = timeLine.indexOf("-->");
      if (arrow === -1) continue;
      const start = parseVttTimestamp(timeLine.slice(0, arrow));
      const rest = timeLine.slice(arrow + 3).trim();
      const endPart = rest.split(/\s+/)[0];
      const end = parseVttTimestamp(endPart);
      const textLines = lines.slice(i + 1);
      if (!textLines.length) continue;
      out.push({ start, end, text: textLines.join("\n") });
    }
    out.sort((a, b) => a.start - b.start || a.end - b.end);
    return out;
  }

  function findCue(t) {
    // VTT from chunked transcription often has overlapping ranges (long + short cues).
    // Pick the shortest matching span so a 3-minute accidental block does not hide normal lines.
    let best = null;
    let bestDur = Infinity;
    let bestStart = -Infinity;
    for (let i = 0; i < cues.length; i++) {
      const c = cues[i];
      if (t >= c.start && t < c.end) {
        const dur = c.end - c.start;
        if (dur < bestDur || (dur === bestDur && c.start > bestStart)) {
          bestDur = dur;
          bestStart = c.start;
          best = c.text;
        }
      }
    }
    return best != null ? best : "";
  }

  function tick() {
    const box = document.getElementById(CAPTIONS_ID);
    if (!box || !audioEl) return;
    const sw = document.getElementById("switch");
    const off = !sw || sw.textContent.trim() === "off";
    if (off || !isFinite(audioEl.currentTime)) {
      box.textContent = "";
      box.hidden = true;
      return;
    }
    // Main programme not started yet (e.g. radio FX lead-in): do not show cues for paused currentTime.
    if (audioEl.paused || audioEl.ended) {
      box.textContent = "";
      box.hidden = true;
      return;
    }
    const t = audioEl.currentTime;
    const line = findCue(t);
    if (line) {
      box.textContent = line;
      box.hidden = false;
    } else {
      box.textContent = "";
      box.hidden = true;
    }
  }

  function vttUrlFromAudioSrc(src) {
    if (!src) return null;
    const base = src.replace(/^.*\//, "").replace(/\.[^.]+$/, "");
    return "static/captions/" + base + ".vtt";
  }

  function resolveCaptionsUrl(el) {
    const override = el.dataset && el.dataset.captionsSrc;
    if (override && String(override).trim()) {
      return String(override).trim();
    }
    return vttUrlFromAudioSrc(el.getAttribute("src") || el.src);
  }

  window.initVcCaptions = function () {
    audioEl = document.getElementById("audio2");
    if (!audioEl) return;

    const url = resolveCaptionsUrl(audioEl);
    if (!url) return;

    fetch(url, { cache: "force-cache" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(String(r.status)))))
      .then((txt) => {
        cues = parseVtt(txt);
      })
      .catch(() => {
        cues = [];
      });

    audioEl.addEventListener("timeupdate", tick);
    audioEl.addEventListener("seeked", tick);
    audioEl.addEventListener("play", tick);
    audioEl.addEventListener("pause", tick);
    audioEl.addEventListener("playing", tick);
  };
})();
