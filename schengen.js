// The Schengen 90/180 calculator: the counting, then the page around it.
//
// The counting follows the app's SchengenRule exactly, so the site and the app
// never disagree by a day: the window is the 180 days ending on the day asked
// about, the day of entry and the day of exit both count, and the next entry is
// the first day the window has room for one more day.

const ALLOWANCE = 90;
const WINDOW = 180;
const MS_PER_DAY = 86400000;

/// "2026-03-14" to a whole day number, or null. Days, not instants: a date
/// typed in Tokyo and one typed in Lisbon are the same day.
function toDay(text) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text || "");
  if (!match) return null;
  const [, y, m, d] = match.map(Number);
  const time = Date.UTC(y, m - 1, d);
  const back = new Date(time);
  if (back.getUTCFullYear() !== y || back.getUTCMonth() !== m - 1 || back.getUTCDate() !== d) return null;
  return Math.round(time / MS_PER_DAY);
}

function fromDay(day) {
  return new Date(day * MS_PER_DAY).toISOString().slice(0, 10);
}

/// Every day spent in the area, from trips as typed. Overlapping trips are
/// one stay, not two: a set has no way to count a day twice.
function daysIn(trips) {
  const days = new Set();
  for (const trip of trips) {
    const start = toDay(trip.entry), end = toDay(trip.exit);
    if (start === null || end === null || end < start) continue;
    for (let day = start; day <= end; day++) days.add(day);
  }
  return days;
}

function usedOn(days, day) {
  let used = 0;
  for (let d = day - WINDOW + 1; d <= day; d++) if (days.has(d)) used++;
  return used;
}

/// The last day of a stay that starts on `from`, or null when even that first
/// day would be one too many. Planned trips later on still count against it.
function stayUntil(days, from) {
  const staying = new Set(days);
  let last = null;
  for (let day = from; day < from + WINDOW; day++) {
    staying.add(day);
    if (usedOn(staying, day) > ALLOWANCE) break;
    last = day;
  }
  return last;
}

function analyse(trips, reference) {
  const days = daysIn(trips);
  const used = usedOn(days, reference);
  const result = {
    used,
    remaining: Math.max(0, ALLOWANCE - used),
    overstay: Math.max(0, used - ALLOWANCE),
    windowStart: reference - WINDOW + 1,
    reference,
    days,
    stayUntil: stayUntil(days, reference),
    nextEntry: null,
    nextStayUntil: null,
  };
  // As in the app: once nothing is left, the question is when to come back.
  if (result.remaining === 0) {
    for (let day = reference + 1; day <= reference + WINDOW; day++) {
      const there = days.has(day) ? 0 : 1;
      if (usedOn(days, day) + there <= ALLOWANCE) {
        result.nextEntry = day;
        result.nextStayUntil = stayUntil(days, day);
        break;
      }
    }
  }
  return result;
}

if (typeof module !== "undefined") {
  module.exports = { toDay, fromDay, daysIn, usedOn, stayUntil, analyse, ALLOWANCE, WINDOW };
}

// MARK: - The page

const TEXT = {
  en: {
    entry: "Entry",
    exit: "Exit",
    remove: "Remove this trip",
    usedOf: (n) => `${n} of 90`,
    usedLabel: (from, to) => `days used in the 180 days from ${from} to ${to}`,
    left: (n) => `${n} ${n === 1 ? "day" : "days"} left`,
    over: (n) => `${n} ${n === 1 ? "day" : "days"} over the limit`,
    stay: (on, until, n) => `In the area from ${on}, you can stay until <strong>${until}</strong> — ${n} ${n === 1 ? "day" : "days"} in a row.`,
    full: (on) => `On ${on} there is no room left in the window.`,
    next: (on, until, n) => `The next day you can enter is <strong>${on}</strong>, and from then you can stay until ${until} (${n} ${n === 1 ? "day" : "days"}).`,
    nextNone: "No day in the next 180 frees up: the trips you entered fill the window ahead.",
    invalid: "A trip whose exit is before its entry is left out.",
    empty: "Add a trip to see the count.",
    legendUsed: "a day in the area",
    legendToday: "the day you are checking",
  },
  ru: {
    entry: "Въезд",
    exit: "Выезд",
    remove: "Убрать поездку",
    usedOf: (n) => `${n} из 90`,
    usedLabel: (from, to) => `дней использовано за 180 дней с ${from} по ${to}`,
    left: (n) => `${n} ${ruDays(n)} в запасе`,
    over: (n) => `превышение на ${n} ${ruDays(n)}`,
    stay: (on, until, n) => `Если вы в Шенгене с ${on}, можно оставаться до <strong>${until}</strong> включительно — ${n} ${ruDays(n)} подряд.`,
    full: (on) => `На ${on} в окне не осталось ни одного дня.`,
    next: (on, until, n) => `Въехать снова можно <strong>${on}</strong>, и с этого дня оставаться до ${until} (${n} ${ruDays(n)}).`,
    nextNone: "В ближайшие 180 дней окно не освобождается: его заполняют введённые поездки.",
    invalid: "Поездка, где выезд раньше въезда, не учитывается.",
    empty: "Добавьте поездку, чтобы увидеть подсчёт.",
    legendUsed: "день в Шенгене",
    legendToday: "день проверки",
  },
};

function ruDays(n) {
  const form = new Intl.PluralRules("ru").select(n);
  return form === "one" ? "день" : form === "few" ? "дня" : "дней";
}

function startPage() {
  const root = document.getElementById("calculator");
  if (!root) return;
  const lang = document.documentElement.lang.startsWith("ru") ? "ru" : "en";
  const t = TEXT[lang];
  const format = new Intl.DateTimeFormat(lang === "ru" ? "ru-RU" : "en-GB",
    { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const say = (day) => format.format(new Date(day * MS_PER_DAY));

  const list = root.querySelector("[data-trips]");
  const check = root.querySelector("[data-check]");
  const output = root.querySelector("[data-result]");
  const storeKey = "presence-schengen-trips";

  const today = Math.floor((Date.now() - new Date().getTimezoneOffset() * 60000) / MS_PER_DAY);
  check.value = fromDay(today);

  // Kept in this browser only, so a returning visitor finds their trips; the
  // page works the same when storage is refused.
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(storeKey) || "[]"); } catch (_) {}
  if (!Array.isArray(saved) || saved.length === 0) saved = [{ entry: "", exit: "" }];
  saved.forEach(addRow);

  root.querySelector("[data-add]").addEventListener("click", () => {
    addRow({ entry: "", exit: "" });
    list.lastElementChild.querySelector("input").focus();
  });
  check.addEventListener("input", update);
  update();

  function addRow(trip) {
    const row = document.createElement("div");
    row.className = "trip-row";
    row.innerHTML = `
      <label><span>${t.entry}</span><input type="date" data-entry></label>
      <label><span>${t.exit}</span><input type="date" data-exit></label>
      <button type="button" class="trip-remove" aria-label="${t.remove}">×</button>`;
    row.querySelector("[data-entry]").value = trip.entry || "";
    row.querySelector("[data-exit]").value = trip.exit || "";
    row.addEventListener("input", (event) => {
      // An exit comes after its entry, so its picker starts there.
      const entry = row.querySelector("[data-entry]");
      if (event.target === entry) row.querySelector("[data-exit]").min = entry.value;
      update();
    });
    row.querySelector(".trip-remove").addEventListener("click", () => {
      row.remove();
      if (!list.children.length) addRow({ entry: "", exit: "" });
      update();
    });
    list.appendChild(row);
  }

  function trips() {
    return [...list.children].map((row) => ({
      entry: row.querySelector("[data-entry]").value,
      exit: row.querySelector("[data-exit]").value,
    }));
  }

  function update() {
    const all = trips();
    try { localStorage.setItem(storeKey, JSON.stringify(all)); } catch (_) {}
    const reference = toDay(check.value);
    const complete = all.filter((trip) => toDay(trip.entry) !== null && toDay(trip.exit) !== null);
    if (reference === null || complete.length === 0) {
      output.innerHTML = `<p class="calc-empty">${t.empty}</p>`;
      return;
    }
    const backwards = complete.some((trip) => toDay(trip.exit) < toDay(trip.entry));
    const r = analyse(complete, reference);

    let lines = "";
    if (r.stayUntil !== null) {
      lines += `<p>${t.stay(say(reference), say(r.stayUntil), r.stayUntil - reference + 1)}</p>`;
    } else {
      lines += `<p>${t.full(say(reference))}</p>`;
    }
    if (r.remaining === 0) {
      lines += r.nextEntry !== null
        ? `<p>${t.next(say(r.nextEntry), say(r.nextStayUntil), r.nextStayUntil - r.nextEntry + 1)}</p>`
        : `<p>${t.nextNone}</p>`;
    }
    if (backwards) lines += `<p class="calc-warning">${t.invalid}</p>`;

    let cells = "";
    for (let day = r.windowStart; day <= reference; day++) {
      const kind = (r.days.has(day) ? " used" : "") + (day === reference ? " today" : "");
      cells += `<span class="cell${kind}"></span>`;
    }

    output.innerHTML = `
      <div class="calc-figure${r.overstay ? " over" : ""}">
        <p class="calc-number">${t.usedOf(r.used)}</p>
        <p class="calc-caption">${t.usedLabel(say(r.windowStart), say(reference))}</p>
        <p class="calc-left">${r.overstay ? t.over(r.overstay) : t.left(r.remaining)}</p>
      </div>
      <div class="window-strip" aria-hidden="true">${cells}</div>
      <p class="strip-legend" aria-hidden="true"><span class="cell used"></span> ${t.legendUsed}
        <span class="cell today"></span> ${t.legendToday}</p>
      ${lines}`;
  }
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", startPage);
}
