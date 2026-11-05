// The stay calculators that are not Schengen: a country's visa-free limit,
// and the 183-day count for tax residency. The counting first, then the page.
//
// Days are counted the way the app and the Schengen page count them: the day
// of entry and the day of exit are both days in the country, and trips that
// overlap are one stay. A limit is any of the shapes a border actually uses,
// which are the app's StayAllowance shapes: so many days per entry, so many in
// any window of so many days, or both at once.

const MS_PER_DAY = 86400000;

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

function civil(day) {
  const date = new Date(day * MS_PER_DAY);
  return { y: date.getUTCFullYear(), m: date.getUTCMonth() + 1, d: date.getUTCDate() };
}

function dayOf(y, m, d) {
  return Math.round(Date.UTC(y, m - 1, d) / MS_PER_DAY);
}

function daysIn(trips) {
  const days = new Set();
  for (const trip of trips) {
    const start = toDay(trip.entry), end = toDay(trip.exit);
    if (start === null || end === null || end < start) continue;
    for (let day = start; day <= end; day++) days.add(day);
  }
  return days;
}

function countIn(days, first, last) {
  let count = 0;
  for (let d = first; d <= last; d++) if (days.has(d)) count++;
  return count;
}

// MARK: - A visa-free limit

/// The first day of the unbroken run of days that reaches `day`, counting
/// `day` itself as spent: a stay continued is one entry, not a new one.
function runStart(days, day) {
  let start = day;
  while (days.has(start - 1)) start--;
  return start;
}

/// Whether one more day on `day` keeps within the rule, with `days` already
/// holding everything spent and planned.
function allowed(rule, days, day) {
  if (rule.perEntry && day - runStart(days, day) + 1 > rule.perEntry) return false;
  if (rule.allowance && countIn(days, day - rule.window + 1, day) > rule.allowance) return false;
  return true;
}

/// The last day of a stay that goes on from `from`, or null when `from`
/// itself would break the rule.
function stayUntil(rule, days, from) {
  const staying = new Set(days);
  const horizon = Math.max(rule.perEntry || 0, rule.window || 0) + 1;
  let last = null;
  for (let day = from; day < from + horizon; day++) {
    staying.add(day);
    if (!allowed(rule, staying, day)) break;
    last = day;
  }
  return last;
}

function analyseStay(rule, trips, reference) {
  const days = daysIn(trips);
  const result = { reference, days, rule };
  if (rule.allowance) {
    result.windowStart = reference - rule.window + 1;
    result.used = countIn(days, result.windowStart, reference);
    result.remaining = Math.max(0, rule.allowance - result.used);
    result.overstay = Math.max(0, result.used - rule.allowance);
  }
  if (rule.perEntry) {
    // The visit going on, if the traveller is there on the day checked.
    result.entry = days.has(reference) ? runStart(days, reference) : null;
    result.visitDays = result.entry === null ? 0 : reference - result.entry + 1;
    result.visitOver = Math.max(0, result.visitDays - rule.perEntry);
  }
  result.stayUntil = stayUntil(rule, days, reference);
  result.nextEntry = null;
  if (result.stayUntil === null || (rule.allowance && result.remaining === 0)) {
    // A fresh entry. Under a per-entry limit it has to follow a day away, or
    // it is the same visit going on; a window alone does not care.
    const horizon = (rule.window || rule.perEntry) + 1;
    for (let day = reference + 1; day <= reference + horizon; day++) {
      if (rule.perEntry && (days.has(day) || days.has(day - 1))) continue;
      const trial = new Set(days);
      trial.add(day);
      if (allowed(rule, trial, day)) {
        result.nextEntry = day;
        result.nextStayUntil = stayUntil(rule, days, day);
        break;
      }
    }
  }
  return result;
}

// MARK: - 183 days

/// The period a tax count runs over: the tax year that holds `reference`,
/// starting on `start` ("01-01", "04-06", ...), or with `start` null, the
/// twelve months ending on it.
function taxPeriod(start, reference) {
  const c = civil(reference);
  if (!start) {
    // Twelve months back to the day after: 15 March 2026 looks back to
    // 16 March 2025. The 29th of February steps back to the 1st of March.
    const back = dayOf(c.y - 1, c.m, c.d);
    const sameDate = civil(back).d === c.d;
    return { first: sameDate ? back + 1 : back, last: reference };
  }
  const [m, d] = start.split("-").map(Number);
  let first = dayOf(c.y, m, d);
  if (first > reference) first = dayOf(c.y - 1, m, d);
  const f = civil(first);
  return { first, last: dayOf(f.y + 1, m, d) - 1 };
}

function analyseTax(threshold, start, trips, reference) {
  const days = daysIn(trips);
  const period = taxPeriod(start, reference);
  const sofar = countIn(days, period.first, reference);
  const total = countIn(days, period.first, period.last);
  const result = {
    days, period, reference, threshold, sofar, total,
    // Whole period, planned trips included, for a tax year; to today for a
    // rolling year, which ends on the day checked.
    counted: start ? total : sofar,
    reached: null,
  };
  result.left = Math.max(0, threshold - result.counted);
  // If the traveller stays from the day checked on: the day the count reaches
  // the threshold, within the period (a tax year) or a year ahead (rolling).
  const staying = new Set(days);
  const horizon = start ? period.last : reference + 366;
  for (let day = reference; day <= horizon; day++) {
    staying.add(day);
    const p = start ? period : taxPeriod(null, day);
    if (countIn(staying, p.first, start ? day : p.last) >= threshold) {
      result.reached = day;
      break;
    }
  }
  return result;
}

if (typeof module !== "undefined") {
  module.exports = { toDay, fromDay, daysIn, analyseStay, stayUntil, taxPeriod, analyseTax };
}

// MARK: - The page

const TEXT = {
  en: {
    entry: "Entry", exit: "Exit", remove: "Remove this trip",
    empty: "Add a trip to see the count.",
    invalid: "A trip whose exit is before its entry is left out.",
    days: (n) => `${n} ${n === 1 ? "day" : "days"}`,
    usedOf: (n, of) => `${n} of ${of}`,
    usedLabel: (window, from, to) => `days in the country in the ${window} days from ${from} to ${to}`,
    left: (n) => `${n} ${n === 1 ? "day" : "days"} left`,
    over: (n) => `${n} ${n === 1 ? "day" : "days"} over the limit`,
    visit: (n, of, since) => `Day ${n} of ${of} of the visit that began on ${since}.`,
    visitOver: (n) => `This visit is ${n} ${n === 1 ? "day" : "days"} past the limit for one entry.`,
    stay: (on, until, n) => `In the country from ${on}, you can stay until <strong>${until}</strong> — ${n} ${n === 1 ? "day" : "days"}, that day included.`,
    full: (on) => `On ${on} the limit leaves no room for another day.`,
    next: (on, until, n) => `The next day you can enter is <strong>${on}</strong>, and from then you can stay until ${until} (${n} ${n === 1 ? "day" : "days"}).`,
    nextNone: "No day in the period ahead frees up: the trips you entered fill it.",
    taxNumber: (n, of) => `${n} of ${of}`,
    taxLabel: (from, to) => `days in the country from ${from} to ${to}`,
    taxLeft: (n) => `${n} ${n === 1 ? "day" : "days"} below the threshold`,
    taxOver: "the threshold is reached",
    taxPlanned: (n) => `Of these, ${n} ${n === 1 ? "is" : "are"} after the day checked — trips you planned.`,
    taxReach: (on, n) => `Staying from today, you would reach ${n} days on <strong>${on}</strong>.`,
    taxNoReach: (to) => `Staying from today, you would not reach the threshold by ${to}.`,
    legendUsed: "a day in the country", legendToday: "the day you are checking",
  },
  ru: {
    entry: "Въезд", exit: "Выезд", remove: "Убрать поездку",
    empty: "Добавьте поездку, чтобы увидеть подсчёт.",
    invalid: "Поездка, где выезд раньше въезда, не учитывается.",
    days: (n) => `${n} ${ruDays(n)}`,
    usedOf: (n, of) => `${n} из ${of}`,
    usedLabel: (window, from, to) => `дней в стране за ${window} ${ruDays(window)} с ${from} по ${to}`,
    left: (n) => `${n} ${ruDays(n)} в запасе`,
    over: (n) => `превышение на ${n} ${ruDays(n)}`,
    visit: (n, of, since) => `${n}-й день из ${of} в поездке, начавшейся ${since}.`,
    visitOver: (n) => `Эта поездка уже на ${n} ${ruDays(n)} дольше, чем можно за один въезд.`,
    stay: (on, until, n) => `Если вы в стране с ${on}, можно оставаться до <strong>${until}</strong> включительно — ${n} ${ruDays(n)}, считая этот день.`,
    full: (on) => `На ${on} лимит не оставляет ни одного дня.`,
    next: (on, until, n) => `Въехать снова можно <strong>${on}</strong>, и с этого дня оставаться до ${until} (${n} ${ruDays(n)}).`,
    nextNone: "В ближайший период лимит не освобождается: его заполняют введённые поездки.",
    taxNumber: (n, of) => `${n} из ${of}`,
    taxLabel: (from, to) => `дней в стране с ${from} по ${to}`,
    taxLeft: (n) => `до порога ${n} ${ruDays(n)}`,
    taxOver: "порог достигнут",
    taxPlanned: (n) => `Из них ${n} ${ruDays(n)} — после даты проверки: это запланированные поездки.`,
    taxReach: (on, n) => `Если оставаться с даты проверки, ${n} дней наберётся <strong>${on}</strong>.`,
    taxNoReach: (to) => `Если оставаться с даты проверки, порог до ${to} не наберётся.`,
    legendUsed: "день в стране", legendToday: "день проверки",
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
  const mode = root.dataset.mode;

  const list = root.querySelector("[data-trips]");
  const check = root.querySelector("[data-check]");
  const output = root.querySelector("[data-result]");
  const picker = root.querySelector("[data-rule]");
  const custom = root.querySelector("[data-custom]");
  const storeKey = "presence-trips-" + root.dataset.store;

  const today = Math.floor((Date.now() - new Date().getTimezoneOffset() * 60000) / MS_PER_DAY);
  check.value = fromDay(today);

  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(storeKey) || "[]"); } catch (_) {}
  if (!Array.isArray(saved) || saved.length === 0) saved = [{ entry: "", exit: "" }];
  saved.forEach(addRow);

  root.querySelector("[data-add]").addEventListener("click", () => {
    addRow({ entry: "", exit: "" });
    list.lastElementChild.querySelector("input").focus();
  });
  root.addEventListener("input", update);
  root.addEventListener("change", update);
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
      const entry = row.querySelector("[data-entry]");
      if (event.target === entry) row.querySelector("[data-exit]").min = entry.value;
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

  /// The rule chosen, from the option's data or, for "my own", the fields.
  function rule() {
    const option = picker.selectedOptions[0];
    const isCustom = option.value === "custom";
    if (custom) custom.hidden = !isCustom;
    const source = isCustom ? null : option.dataset;
    const read = (name) => {
      const value = isCustom ? custom.querySelector(`[name="${name}"]`).value : source[name];
      const number = parseInt(value, 10);
      return number > 0 ? number : null;
    };
    if (mode === "tax") {
      return { threshold: read("threshold") || 183, start: isCustom ? null : (source.start || null) };
    }
    const r = { perEntry: read("perEntry"), allowance: read("allowance"), window: read("window") };
    if (!r.allowance || !r.window || r.allowance > r.window) { r.allowance = null; r.window = null; }
    return r;
  }

  function strip(first, last, days, reference) {
    let cells = "";
    for (let day = first; day <= last; day++) {
      const kind = (days.has(day) ? " used" : "") + (day === reference ? " today" : "") +
        (day > reference ? " ahead" : "");
      cells += `<span class="cell${kind}"></span>`;
    }
    return `<div class="window-strip" aria-hidden="true">${cells}</div>
      <p class="strip-legend" aria-hidden="true"><span class="cell used"></span> ${t.legendUsed}
        <span class="cell today"></span> ${t.legendToday}</p>`;
  }

  function update() {
    const all = trips();
    try { localStorage.setItem(storeKey, JSON.stringify(all)); } catch (_) {}
    const reference = toDay(check.value);
    const complete = all.filter((trip) => toDay(trip.entry) !== null && toDay(trip.exit) !== null);
    const chosen = rule();
    if (reference === null || complete.length === 0 ||
        (mode !== "tax" && !chosen.perEntry && !chosen.allowance)) {
      output.innerHTML = `<p class="calc-empty">${t.empty}</p>`;
      return;
    }
    const backwards = complete.some((trip) => toDay(trip.exit) < toDay(trip.entry));
    output.innerHTML = (mode === "tax" ? taxView(chosen, complete, reference) : stayView(chosen, complete, reference)) +
      (backwards ? `<p class="calc-warning">${t.invalid}</p>` : "");
  }

  function stayView(chosen, complete, reference) {
    const r = analyseStay(chosen, complete, reference);
    let figure = "", lines = "";
    if (chosen.allowance) {
      figure = `
        <div class="calc-figure${r.overstay ? " over" : ""}">
          <p class="calc-number">${t.usedOf(r.used, chosen.allowance)}</p>
          <p class="calc-caption">${t.usedLabel(chosen.window, say(r.windowStart), say(reference))}</p>
          <p class="calc-left">${r.overstay ? t.over(r.overstay) : t.left(r.remaining)}</p>
        </div>`;
    } else if (chosen.perEntry) {
      const left = Math.max(0, chosen.perEntry - r.visitDays);
      figure = `
        <div class="calc-figure${r.visitOver ? " over" : ""}">
          <p class="calc-number">${t.usedOf(r.visitDays, chosen.perEntry)}</p>
          <p class="calc-caption">${r.entry !== null ? t.visit(r.visitDays, chosen.perEntry, say(r.entry)) : ""}</p>
          <p class="calc-left">${r.visitOver ? t.over(r.visitOver) : t.left(left)}</p>
        </div>`;
    }
    if (chosen.allowance && chosen.perEntry && r.entry !== null) {
      lines += `<p>${r.visitOver ? t.visitOver(r.visitOver) : t.visit(r.visitDays, chosen.perEntry, say(r.entry))}</p>`;
    } else if (!chosen.allowance && r.visitOver) {
      lines += `<p>${t.visitOver(r.visitOver)}</p>`;
    }
    lines += r.stayUntil !== null
      ? `<p>${t.stay(say(reference), say(r.stayUntil), r.stayUntil - reference + 1)}</p>`
      : `<p>${t.full(say(reference))}</p>`;
    if (r.stayUntil === null || (chosen.allowance && r.remaining === 0)) {
      lines += r.nextEntry !== null
        ? `<p>${t.next(say(r.nextEntry), say(r.nextStayUntil), r.nextStayUntil - r.nextEntry + 1)}</p>`
        : `<p>${t.nextNone}</p>`;
    }
    const first = chosen.allowance ? r.windowStart : reference - Math.min(chosen.perEntry, 365) + 1;
    return figure + strip(first, reference, r.days, reference) + lines;
  }

  function taxView(chosen, complete, reference) {
    const r = analyseTax(chosen.threshold, chosen.start, complete, reference);
    const reached = r.counted >= chosen.threshold;
    let lines = "";
    if (chosen.start && r.total > r.sofar) lines += `<p>${t.taxPlanned(r.total - r.sofar)}</p>`;
    if (!reached) {
      lines += r.reached !== null
        ? `<p>${t.taxReach(say(r.reached), chosen.threshold)}</p>`
        : `<p>${t.taxNoReach(say(chosen.start ? r.period.last : reference + 366))}</p>`;
    }
    return `
      <div class="calc-figure${reached ? " over" : ""}">
        <p class="calc-number">${t.taxNumber(r.counted, chosen.threshold)}</p>
        <p class="calc-caption">${t.taxLabel(say(r.period.first), say(chosen.start ? r.period.last : reference))}</p>
        <p class="calc-left">${reached ? t.taxOver : t.taxLeft(r.left)}</p>
      </div>
      ${strip(r.period.first, r.period.last, r.days, reference)}
      ${lines}`;
  }
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", startPage);
}
