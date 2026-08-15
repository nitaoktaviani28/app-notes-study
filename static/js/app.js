const clock = document.getElementById("clock");
const dateText = document.getElementById("dateText");

function updateClock() {
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("id-ID", { hour12: false });
  dateText.textContent = now.toLocaleDateString("id-ID", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric"
  });
}

setInterval(updateClock, 1000);
updateClock();

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
}

const pomodoroDisplay = document.getElementById("pomodoroTimer");
const pomodoroStart = document.getElementById("startPomodoro");
let pomodoroSecs = 25 * 60;
let pomodoroInterval;

function drawPomodoro() {
  const m = String(Math.floor(pomodoroSecs / 60)).padStart(2, "0");
  const s = String(pomodoroSecs % 60).padStart(2, "0");
  pomodoroDisplay.textContent = `${m}:${s}`;
}

drawPomodoro();

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
