const clock = document.getElementById("clock");
const dateText = document.getElementById("dateText");
const themeToggle = document.getElementById("themeToggle");
const isHomePage = Boolean(document.querySelector(".app-shell"));
const savedTheme = localStorage.getItem("complite-theme") || "light";
const featureButtons = document.querySelectorAll(".feature-btn[data-target]");
const panels = document.querySelectorAll(".panel");
const breakInput = document.querySelector("input[name='break_minutes']");
const breakInfo = document.getElementById("breakInfo");

if (isHomePage) {
  document.body.setAttribute("data-theme", savedTheme);
} else {
  document.body.removeAttribute("data-theme");
}

if (themeToggle && isHomePage) {
  themeToggle.textContent = savedTheme === "dark" ? "Light" : "Dark";
  themeToggle.addEventListener("click", () => {
    const current = document.body.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    document.body.setAttribute("data-theme", next);
    localStorage.setItem("complite-theme", next);
    themeToggle.textContent = next === "dark" ? "Light" : "Dark";
  });
}

function activatePanel(targetId) {
  if (!targetId) {
    return;
  }

  panels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === targetId);
  });

  featureButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.target === targetId);
  });

  if (themeToggle) {
    themeToggle.style.display = targetId === "dashboardPanel" ? "inline-block" : "none";
  }

  if (targetId === "schedulePanel" && window.compliteCalendar) {
    window.compliteCalendar.updateSize();
  }
}

featureButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    activatePanel(btn.dataset.target);
  });
});

function updateClock() {
  if (!clock || !dateText) {
    return;
  }
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("id-ID", { hour12: false });
  dateText.textContent = now.toLocaleDateString("id-ID", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric"
  });
}

if (clock && dateText) {
  setInterval(updateClock, 1000);
  updateClock();
}

const calendarEl = document.getElementById("calendar");
if (calendarEl) {
  const addMinutesToLocalIso = (startIso, extraMinutes) => {
    const [datePart, timePart] = startIso.split("T");
    if (!datePart || !timePart) {
      return startIso;
    }
    const [hourRaw, minuteRaw] = timePart.split(":");
    const baseMinutes = Number(hourRaw) * 60 + Number(minuteRaw);
    const totalMinutes = baseMinutes + Number(extraMinutes || 0);
    const safeMinutes = totalMinutes < 0 ? 0 : totalMinutes;
    const newHour = String(Math.floor((safeMinutes % (24 * 60)) / 60)).padStart(2, "0");
    const newMinute = String(safeMinutes % 60).padStart(2, "0");
    return `${datePart}T${newHour}:${newMinute}:00`;
  };

  const preparedEvents = (window.calendarItems || []).map((event) => {
    if (event.start && !event.end && event.durationMinutes) {
      return {
        ...event,
        end: addMinutesToLocalIso(event.start, event.durationMinutes)
      };
    }
    return event;
  });

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    height: 650,
    allDaySlot: false,
    expandRows: true,
    slotMinTime: "00:00:00",
    slotMaxTime: "22:00:00",
    nowIndicator: true,
    displayEventTime: true,
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    dayMaxEventRows: 3,
    locale: "id",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "timeGridWeek,dayGridMonth"
    },
    eventDidMount: (info) => {
      const location = info.event.extendedProps.location;
      const note = info.event.extendedProps.note;
      const extra = [location, note].filter((v) => v && v !== "-").join(" | ");
      if (extra) {
        info.el.title = `${info.event.title} | ${extra}`;
      }
    },
    eventContent: (arg) => {
      const note = arg.event.extendedProps.note;
      const location = arg.event.extendedProps.location;
      const pieces = [];
      if (location && location !== "-") {
        pieces.push(location);
      }
      if (note && note !== "-") {
        pieces.push(note);
      }
      const noteText = pieces.join(" | ");
      const timeText = arg.timeText ? `<div class=\"fc-event-time-line\">${arg.timeText}</div>` : "";
      const detailText = noteText ? `<div class=\"fc-event-note-line\">${noteText}</div>` : "";
      return {
        html: `<div class=\"fc-event-main-wrap\"><div class=\"fc-event-title-line\">${arg.event.title}</div>${timeText}${detailText}</div>`
      };
    },
    events: preparedEvents
  });
  calendar.render();
  window.compliteCalendar = calendar;
}

const pomodoroDisplay = document.getElementById("pomodoroTimer");
const pomodoroStart = document.getElementById("startPomodoro");
const focusPreset = document.getElementById("focusPreset");
let pomodoroSecs = 25 * 60;
let pomodoroInterval;

function drawPomodoro() {
  if (!pomodoroDisplay) {
    return;
  }
  const m = String(Math.floor(pomodoroSecs / 60)).padStart(2, "0");
  const s = String(pomodoroSecs % 60).padStart(2, "0");
  pomodoroDisplay.textContent = `${m}:${s}`;
}

if (pomodoroDisplay) {
  drawPomodoro();
}

if (focusPreset) {
  focusPreset.addEventListener("change", () => {
    const picked = Number(focusPreset.value || 25);
    pomodoroSecs = picked * 60;
    drawPomodoro();
  });
}

function updateBreakInfo() {
  if (!breakInfo || !breakInput) {
    return;
  }
  const minutes = Number(breakInput.value || 0);
  breakInfo.textContent = `Istirahat: ${minutes} menit`;
}

if (breakInput) {
  breakInput.addEventListener("input", updateBreakInfo);
  updateBreakInfo();
}

if (pomodoroStart) {
  pomodoroStart.addEventListener("click", () => {
    if (focusPreset) {
      pomodoroSecs = Number(focusPreset.value || 25) * 60;
      drawPomodoro();
    }
    clearInterval(pomodoroInterval);
    pomodoroInterval = setInterval(() => {
      pomodoroSecs -= 1;
      drawPomodoro();
      if (pomodoroSecs <= 0) {
        clearInterval(pomodoroInterval);
        alert("Sesi fokus selesai. Waktunya istirahat!");
        pomodoroSecs = 25 * 60;
        drawPomodoro();
      }
    }, 1000);
  });
}
