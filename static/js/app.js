const clock = document.getElementById("clock");
const dateText = document.getElementById("dateText");
const themeToggle = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("complite-theme") || "light";
const featureButtons = document.querySelectorAll(".feature-btn[data-target]");
const panels = document.querySelectorAll(".panel");

document.body.setAttribute("data-theme", savedTheme);

if (themeToggle) {
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
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    height: 580,
    locale: "id",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "timeGridWeek,dayGridMonth"
    },
    events: window.calendarItems || []
  });
  calendar.render();
  window.compliteCalendar = calendar;
}

const pomodoroDisplay = document.getElementById("pomodoroTimer");
const pomodoroStart = document.getElementById("startPomodoro");
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

if (pomodoroStart) {
  pomodoroStart.addEventListener("click", () => {
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
