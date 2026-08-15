const clock = document.getElementById("clock");
const dateText = document.getElementById("dateText");
const themeToggle = document.getElementById("themeToggle");
const isHomePage = Boolean(document.querySelector(".app-shell"));
const savedTheme = localStorage.getItem("complite-theme") || "light";
const featureButtons = document.querySelectorAll(".feature-btn[data-target]");
const panels = document.querySelectorAll(".panel");
const PANEL_KEY = "complite-last-panel";
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

  localStorage.setItem(PANEL_KEY, targetId);
}

featureButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    activatePanel(btn.dataset.target);
  });
});

const currentParams = new URLSearchParams(window.location.search);
const panelFromQuery = currentParams.get("panel");
const savedPanel = localStorage.getItem(PANEL_KEY);
const initialPanel = panelFromQuery || savedPanel || "dashboardPanel";
activatePanel(initialPanel);

document.querySelectorAll(".panel form").forEach((form) => {
  form.addEventListener("submit", () => {
    const parentPanel = form.closest(".panel");
    if (parentPanel?.id) {
      localStorage.setItem(PANEL_KEY, parentPanel.id);
    }
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
    slotMaxTime: "23:30:00",
    slotDuration: "00:15:00",
    slotLabelInterval: "00:30:00",
    eventMinHeight: 18,
    eventShortHeight: 16,
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
      if (arg.view.type === "dayGridMonth") {
        const compactText = arg.timeText ? `${arg.timeText} ${arg.event.title}` : arg.event.title;
        return {
          html: `<div class="fc-event-compact">${compactText}</div>`
        };
      }

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

function parseQuizBlocks(rawText) {
  if (!rawText || typeof rawText !== "string") {
    return [];
  }

  const normalized = rawText.replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return [];
  }

  const chunks = normalized
    .split(/\n(?=\d+\)\s)/g)
    .map((item) => item.trim())
    .filter(Boolean);

  return chunks.map((chunk) => {
    const firstLine = chunk.split("\n")[0] || "";
    const question = firstLine.replace(/^\d+\)\s*/, "").trim() || "Soal";

    const options = {};
    const optionRegex = /^\s*([ABCD])[\).:\-]\s*(.+)$/gim;
    let match;
    while ((match = optionRegex.exec(chunk)) !== null) {
      options[match[1].toUpperCase()] = match[2].trim();
    }

    const answerMatch = chunk.match(/Jawaban\s*:\s*([ABCD])/i);
    const explanationMatch = chunk.match(/Penjelasan(?:\s+singkat)?\s*:\s*([\s\S]*)/i);

    return {
      question,
      options,
      answer: answerMatch ? answerMatch[1].toUpperCase() : "",
      explanation: explanationMatch ? explanationMatch[1].trim() : "Tidak ada penjelasan dari AI."
    };
  });
}

function renderQuizInteractive() {
  const quizBoxes = document.querySelectorAll(".quiz-box[data-quiz-content]");
  if (!quizBoxes.length) {
    return;
  }

  quizBoxes.forEach((box) => {
    const renderTarget = box.querySelector(".quiz-render");
    const fallback = box.querySelector(".quiz-fallback");
    if (!renderTarget) {
      return;
    }

    let decoded = box.dataset.quizContent || "";
    try {
      decoded = JSON.parse(decoded);
    } catch (_error) {
      // Keep original value when the content is already plain text.
    }

    const quizItems = parseQuizBlocks(decoded);
    if (!quizItems.length) {
      if (fallback) {
        fallback.hidden = false;
      }
      return;
    }

    renderTarget.innerHTML = "";
    const choiceKeys = ["A", "B", "C", "D"];

    quizItems.forEach((item, index) => {
      const wrapper = document.createElement("section");
      wrapper.className = "quiz-item";

      const title = document.createElement("p");
      title.className = "quiz-question";
      title.textContent = `${index + 1}. ${item.question}`;
      wrapper.appendChild(title);

      const choices = document.createElement("div");
      choices.className = "quiz-choices";

      const feedback = document.createElement("div");
      feedback.className = "quiz-feedback";
      feedback.textContent = "Pilih jawaban A/B/C/D untuk cek hasil.";

      choiceKeys.forEach((key) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-choice";
        const optText = item.options[key] || `Pilihan ${key}`;
        btn.textContent = `${key}. ${optText}`;

        btn.addEventListener("click", () => {
          const isCorrect = item.answer === key && Boolean(item.answer);
          choices.querySelectorAll(".quiz-choice").forEach((choiceEl) => {
            choiceEl.classList.remove("is-correct", "is-wrong");
          });

          if (isCorrect) {
            btn.classList.add("is-correct");
            feedback.innerHTML = `<strong>Benar.</strong> ${item.explanation}`;
            feedback.classList.remove("wrong");
            feedback.classList.add("correct");
            return;
          }

          btn.classList.add("is-wrong");
          const correctText = item.options[item.answer] || "Jawaban tidak tersedia";
          const answerLabel = item.answer || "-";
          feedback.innerHTML = `<strong>Belum tepat.</strong> Jawaban benar: ${answerLabel}. ${correctText}. ${item.explanation}`;
          feedback.classList.remove("correct");
          feedback.classList.add("wrong");
        });

        choices.appendChild(btn);
      });

      wrapper.appendChild(choices);
      wrapper.appendChild(feedback);
      renderTarget.appendChild(wrapper);
    });
  });
}

renderQuizInteractive();

function setupMaterialFilter() {
  const filter = document.getElementById("materialFilter");
  const items = document.querySelectorAll(".material-item[data-material-id]");
  if (!filter || !items.length) {
    return;
  }

  const applyFilter = () => {
    const picked = filter.value;
    items.forEach((item) => {
      const materialId = item.dataset.materialId;
      const visible = picked === "all" || materialId === picked;
      item.style.display = visible ? "list-item" : "none";
    });
  };

  filter.addEventListener("change", applyFilter);
  applyFilter();
}

setupMaterialFilter();
