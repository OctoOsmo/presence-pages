#!/usr/bin/env python3
"""Writes the stay calculators that share one layout: a country's visa-free
limit, and the 183-day tax count. The Schengen pages are written by hand.

    python3 tools/build-pages.py

Rules change. Each page says the day they were checked (CHECKED) and sends the
reader to the country's own sources; change a rule here, then run this again.
"""
import html
import json
from pathlib import Path

SITE = "https://octoosmo.github.io/presence-pages/"
ROOT = Path(__file__).resolve().parent.parent
CHECKED = {"en": "5 November 2026", "ru": "5 ноября 2026"}

# MARK: - Words shared by every page

COMMON = {
    "en": {
        "nav": "Primary navigation", "support": "Support", "privacy": "Privacy",
        "rule": "Your passport or rule", "custom": "My own rule",
        "perEntry": "Days per entry", "allowance": "Days allowed", "window": "In any … days",
        "threshold": "Threshold, days",
        "trips": "Your trips", "add": "+ Add a trip", "check": "Date to check",
        "checkHint": "Today, or the day you plan to enter.",
        "tripsHint": "Every stay in the country, with the day you entered and the day you left. Both count as days in the country.",
        "ctaTitle": "Your photos already know these dates",
        "cta": "Typing trips in from memory is where a count goes wrong. Presence, for iPhone and iPad, reads the dates and places your camera already saved and works out every day in every country — then keeps the count of each limit up to date, the visa on your own passport included, and tells you before it runs out. On your device, without an account.",
        "button": "Get Presence on the App Store",
        "shots": [("03-rules.png", "Presence's Rules screen: each limit with the days used and left.", "Every limit counted by itself."),
                  ("01-timeline.png", "The timeline: the country you are in now and every country by days spent.", "Every country you have been to, from your photos."),
                  ("07-trips.png", "The same days grouped as trips, each with its dates and countries.", "Your trips with their dates — nothing to type in.")],
        "shotsDir": "shots/",
        "checked": "Rules as checked on {date}. They change — the country's foreign ministry or embassy has the final word, and this page is a calculator, not legal advice.",
        "related": "Other calculators", "schengen": "Schengen 90/180",
        "lang": "По-русски",
    },
    "ru": {
        "nav": "Навигация", "support": "Поддержка", "privacy": "Конфиденциальность",
        "rule": "Ваш паспорт или правило", "custom": "Своё правило",
        "perEntry": "Дней за въезд", "allowance": "Дней можно", "window": "За любые … дней",
        "threshold": "Порог, дней",
        "trips": "Ваши поездки", "add": "+ Добавить поездку", "check": "Дата проверки",
        "checkHint": "Сегодня или день, когда вы собираетесь въехать.",
        "tripsHint": "Каждое пребывание в стране: день въезда и день выезда. Оба считаются днями в стране.",
        "ctaTitle": "Эти даты уже есть в ваших фото",
        "cta": "Поездки, вбитые по памяти, — главная причина ошибок в подсчёте. Presence для iPhone и iPad читает даты и места, которые уже сохранила камера, и считает каждый день в каждой стране. Потом сам ведёт счёт по каждому лимиту — и по визе в вашем паспорте тоже — и предупреждает до того, как он закончится. Всё на устройстве, без аккаунта.",
        "button": "Скачать Presence в App Store",
        "shots": [("03-rules.png", "Экран «Правила» в Presence: каждый лимит с использованными и оставшимися днями.", "Каждый лимит считается сам."),
                  ("01-timeline.png", "Таймлайн: страна, где вы сейчас, и все страны по числу дней.", "Все страны, где вы были, — по вашим фото."),
                  ("07-trips.png", "Те же дни, сгруппированные в поездки: даты и страны каждой.", "Поездки с датами — ничего не нужно вводить.")],
        "shotsDir": "shots/ru/",
        "checked": "Правила проверены {date}. Они меняются: последнее слово за МИД или посольством страны, а эта страница — калькулятор, а не юридическая консультация.",
        "related": "Другие калькуляторы", "schengen": "Шенген 90/180",
        "lang": "English",
    },
}

# MARK: - The pages

# A preset is (label, rule); a rule is perEntry, allowance and window for a
# stay, threshold and start ("MM-DD", or "" for any twelve months) for tax.
PAGES = [
    {
        "key": "tax", "mode": "tax",
        "slug": {"en": "tax-residency-calculator/", "ru": "ru/kalkulyator-183-dnej/"},
        "en": {
            "title": "183-Day Tax Residency Calculator — days in a country this tax year",
            "description": "Free 183-day calculator: enter your trips to a country and see how many days you have spent there this tax year or in any 12 months, how many are left before 183, and the day you would reach it. Runs in your browser.",
            "eyebrow": "183-day calculator",
            "h1": "How close are you to 183 days?",
            "lede": "Enter your trips to one country. The calculator counts your days there over the tax year or over any twelve months in a row, says how far you are from the threshold, and on which day you would reach it if you stayed. It runs in your browser: nothing you type is sent anywhere.",
            "presets": [
                ("Calendar year, from 1 January", {"threshold": 183, "start": "01-01"}),
                ("Any 12 months in a row", {"threshold": 183, "start": ""}),
                ("Tax year from 6 April (United Kingdom)", {"threshold": 183, "start": "04-06"}),
                ("Tax year from 1 July (Australia)", {"threshold": 183, "start": "07-01"}),
            ],
            "custom": "custom-threshold",
            "faq": [
                ("What is the 183-day rule?", "Many countries treat someone who spends 183 days or more there in a tax year, or in a twelve-month period, as tax resident. It is a rule of thumb, not the whole test: ties such as a home, family, work and where your life is centred can make you resident with fewer days, and a treaty between two countries decides when both claim you."),
                ("Calendar year or any twelve months?", "It depends on the country. Some count the calendar year; others count any twelve consecutive months, so 183 days can be reached across New Year. Russia counts 183 days in twelve consecutive months, with the final status settled for the calendar year; Georgia counts any continuous twelve months that end in the tax year. The UK and Australia run their own tax years. Pick the period your country uses."),
                ("Do the days of arrival and departure count?", "Here, yes: every day you were in the country counts as a day, as most countries count them. Not all do — the UK counts the days you were there at midnight, and the US uses its own weighted three-year test — so check how your country counts before relying on a close number."),
                ("Why does the number include trips I have not taken yet?", "For a tax year, a trip you plan later in the same year counts towards it, so the calculator shows the whole year. For any twelve months, it counts the twelve months ending on the day you check."),
            ],
        },
        "ru": {
            "title": "Калькулятор 183 дней — налоговое резидентство",
            "description": "Бесплатный калькулятор 183 дней: введите поездки в страну и узнайте, сколько дней вы там провели за налоговый год или за любые 12 месяцев, сколько осталось до 183 и когда порог наберётся. Считает в браузере.",
            "eyebrow": "Калькулятор 183 дней",
            "h1": "Сколько вам осталось до 183 дней?",
            "lede": "Введите поездки в одну страну. Калькулятор посчитает дни в ней за налоговый год или за любые 12 месяцев подряд, покажет, сколько осталось до порога, и в какой день он наберётся, если оставаться. Всё считается в браузере: введённое никуда не отправляется.",
            "presets": [
                ("Календарный год, с 1 января", {"threshold": 183, "start": "01-01"}),
                ("Любые 12 месяцев подряд", {"threshold": 183, "start": ""}),
                ("Налоговый год с 6 апреля (Великобритания)", {"threshold": 183, "start": "04-06"}),
                ("Налоговый год с 1 июля (Австралия)", {"threshold": 183, "start": "07-01"}),
            ],
            "custom": "custom-threshold",
            "faq": [
                ("Что такое правило 183 дней?", "Во многих странах налоговым резидентом считают того, кто провёл в стране 183 дня или больше за налоговый год или за 12 месяцев. Это ориентир, а не весь тест: жильё, семья, работа и центр жизненных интересов могут сделать вас резидентом и с меньшим числом дней, а когда на вас претендуют две страны, решает соглашение об избежании двойного налогообложения."),
                ("Календарный год или любые 12 месяцев?", "Зависит от страны. Одни считают календарный год, другие — любые 12 месяцев подряд, и тогда 183 дня могут набраться через Новый год. В России считают 183 дня за 12 следующих подряд месяцев, а окончательный статус определяют по итогам календарного года. В Грузии и Сербии — 183 дня за любые 12 месяцев подряд. У Великобритании и Австралии свои налоговые годы. Выберите период, который использует ваша страна."),
                ("Считаются ли дни въезда и выезда?", "Здесь — да: каждый день, когда вы были в стране, считается днём, как считает большинство стран. Но не все: Великобритания считает дни, когда вы были в стране в полночь, у США свой взвешенный тест за три года. Если число близко к порогу, проверьте, как считает ваша страна."),
                ("Почему в подсчёт попали поездки, которых ещё не было?", "Для налогового года поездка, запланированная на конец того же года, в него войдёт, поэтому калькулятор показывает весь год. Для любых 12 месяцев считаются 12 месяцев, заканчивающиеся датой проверки."),
            ],
        },
    },
    {
        "key": "georgia", "mode": "stay",
        "slug": {"en": "georgia-stay-calculator/", "ru": "ru/kalkulyator-dnej-gruziya/"},
        "en": {
            "title": "Georgia Visa-Free Stay Calculator — the 365-day rule",
            "description": "How long can you stay in Georgia without a visa? Enter your trips and see the day your 365 days end, and how long you can stay if you enter on any date. Works in your browser.",
            "eyebrow": "Georgia stay calculator",
            "h1": "How long can you stay in Georgia?",
            "lede": "Citizens of about ninety-five countries can stay in Georgia for up to a year without a visa. Enter your trips to see how many days of this visit are used and the last day you can stay.",
            "presets": [("Most passports — Russia, Ukraine, Belarus, Kazakhstan, EU, UK, US: 365 days per entry", {"perEntry": 365})],
            "table": [("Russia, Ukraine, Belarus, Kazakhstan, Armenia, Azerbaijan, EU, UK, US, Canada, Israel and others", "365 days from each entry")],
            "faq": [
                ("How does Georgia count the year?", "The 365 days run from the day you enter. Leaving and coming back starts a new count, which is why the rule is usually described as a year per entry rather than days in a window."),
                ("Do frequent border runs cause trouble?", "They can. A new entry is the border officer's decision, and someone who seems to live in Georgia on back-to-back visa-free stays may be asked about it. For a longer life there, a residence permit is the way in."),
                ("Can I work on a visa-free stay?", "Staying visa-free is not the same as being allowed to work. Georgia has been tightening its rules for foreigners who work there, so check what applies to you before you take a job."),
                ("What about tax?", "Georgia makes you tax resident after 183 days in any continuous twelve months ending in the tax year. The 183-day calculator counts that."),
            ],
        },
        "ru": {
            "title": "Сколько можно находиться в Грузии без визы — калькулятор 365 дней",
            "description": "Сколько можно находиться в Грузии без визы? Введите поездки и узнайте, когда заканчиваются ваши 365 дней и сколько можно пробыть, если въехать в любую дату. Считает в браузере.",
            "eyebrow": "Калькулятор дней в Грузии",
            "h1": "Сколько вы можете оставаться в Грузии?",
            "lede": "Граждане примерно 95 стран, включая Россию, могут находиться в Грузии без визы до года. Введите поездки — калькулятор покажет, сколько дней этого визита прошло и до какого числа можно остаться.",
            "presets": [("Большинство паспортов — Россия, Украина, Беларусь, Казахстан, ЕС, Великобритания, США: 365 дней за въезд", {"perEntry": 365})],
            "table": [("Россия, Украина, Беларусь, Казахстан, Армения, Азербайджан, ЕС, Великобритания, США, Канада, Израиль и другие", "365 дней с каждого въезда")],
            "faq": [
                ("Как Грузия считает год?", "365 дней отсчитываются с дня въезда. Если выехать и вернуться, отсчёт начинается заново — поэтому правило обычно описывают как год за въезд, а не дни в окне."),
                ("Не будет ли проблем с частыми визаранами?", "Могут быть. Новый въезд — решение пограничника, и того, кто фактически живёт в Грузии на безвизе подряд, могут расспросить. Чтобы жить там долго, нужен ВНЖ."),
                ("Можно ли работать на безвизе?", "Безвизовое пребывание — не то же самое, что право на работу. Грузия ужесточает правила для работающих иностранцев, поэтому проверьте, что касается вас, прежде чем устраиваться."),
                ("А налоги?", "Налоговым резидентом Грузии становятся после 183 дней за любые 12 месяцев подряд, заканчивающиеся в налоговом году. Это считает калькулятор 183 дней."),
            ],
        },
    },
    {
        "key": "serbia", "mode": "stay",
        "slug": {"en": "serbia-stay-calculator/", "ru": "ru/kalkulyator-dnej-serbiya/"},
        "en": {
            "title": "Serbia Visa-Free Stay Calculator — 30 days for Russians, 90/180 for others",
            "description": "How long can you stay in Serbia without a visa? 30 days from entry for Russian citizens, 90 days in any 180 for EU, UK and US passports. Enter your trips and see the last day you can stay.",
            "eyebrow": "Serbia stay calculator",
            "h1": "How long can you stay in Serbia?",
            "lede": "Serbia's limit depends on your passport: thirty days from each entry for Russian citizens, ninety days in any 180 for most Western passports. Pick yours, enter your trips, and see the last day you can stay.",
            "presets": [
                ("Russia: 30 days from each entry", {"perEntry": 30}),
                ("EU, UK, US and most visa-free passports: 90 days in any 180", {"allowance": 90, "window": 180}),
            ],
            "table": [("Russia", "30 days from the day of entry"),
                      ("EU, Schengen states, UK, US and most other visa-free passports", "90 days in any 180")],
            "faq": [
                ("Does leaving Serbia reset the 30 days?", "For Russian citizens the 30 days run from each entry, so a new entry starts a new count. Border officers can still refuse someone who seems to be living in Serbia on repeated short stays; a residence permit is the way to stay longer."),
                ("How does the 90-in-180 rule work in Serbia?", "Like Schengen's, but on its own: on any day in Serbia, the 180 days ending that day may hold at most 90 in Serbia. Days in the Schengen area do not count towards it."),
                ("Do I need to register?", "Yes. Foreigners register their address with the police within 24 hours of arrival, the 'white card'; a hotel does it for its guests."),
                ("What about tax?", "Serbia treats 183 days in any twelve months as a sign of tax residency. The 183-day calculator counts that."),
            ],
        },
        "ru": {
            "title": "Сколько можно находиться в Сербии без визы — калькулятор 30 дней",
            "description": "Сколько можно быть в Сербии без визы? Россиянам — 30 дней с каждого въезда, паспортам ЕС, Великобритании и США — 90 дней за любые 180. Введите поездки и узнайте, до какого числа можно остаться.",
            "eyebrow": "Калькулятор дней в Сербии",
            "h1": "Сколько вы можете оставаться в Сербии?",
            "lede": "Лимит в Сербии зависит от паспорта: гражданам России — 30 дней с каждого въезда, большинству западных паспортов — 90 дней за любые 180. Выберите свой, введите поездки и узнайте, до какого числа можно остаться.",
            "presets": [
                ("Россия: 30 дней с каждого въезда", {"perEntry": 30}),
                ("ЕС, Великобритания, США и большинство безвизовых паспортов: 90 дней за любые 180", {"allowance": 90, "window": 180}),
            ],
            "table": [("Россия", "30 дней со дня въезда"),
                      ("ЕС, страны Шенгена, Великобритания, США и большинство других безвизовых паспортов", "90 дней за любые 180")],
            "faq": [
                ("Обнуляет ли выезд 30 дней?", "Для граждан России 30 дней отсчитываются с каждого въезда, поэтому новый въезд начинает новый отсчёт. Но пограничник может отказать тому, кто фактически живёт в Сербии короткими заездами подряд; чтобы оставаться дольше, нужен ВНЖ."),
                ("Как работает 90 из 180 в Сербии?", "Как в Шенгене, но отдельно от него: в любой день в Сербии из 180 дней, заканчивающихся этим днём, в Сербии может быть не больше 90. Дни в Шенгене сюда не входят."),
                ("Нужна ли регистрация?", "Да. Иностранец регистрирует адрес в полиции в течение 24 часов после приезда — «белый картон»; за гостей отеля это делает отель."),
                ("А налоги?", "В Сербии признаком налогового резидентства считают 183 дня за любые 12 месяцев. Это считает калькулятор 183 дней."),
            ],
        },
    },
    {
        "key": "turkey", "mode": "stay",
        "slug": {"en": "turkey-stay-calculator/", "ru": "ru/kalkulyator-dnej-turciya/"},
        "en": {
            "title": "Turkey Visa-Free Stay Calculator — 90/180 and 60 days per entry",
            "description": "How long can you stay in Turkey without a visa? 90 days in any 180 for most visa-free passports, and for Russian citizens no more than 60 days per entry as well. Enter your trips and see the last day you can stay.",
            "eyebrow": "Turkey stay calculator",
            "h1": "How long can you stay in Turkey?",
            "lede": "Turkey counts 90 days in any 180 for most visa-free passports, and Russian citizens also may not stay more than 60 days on one entry. Pick your passport, enter your trips, and see the last day you can stay.",
            "presets": [
                ("Russia: 60 days per entry, 90 in any 180", {"perEntry": 60, "allowance": 90, "window": 180}),
                ("Ukraine, EU, UK, US and most visa-free passports: 90 days in any 180", {"allowance": 90, "window": 180}),
            ],
            "table": [("Russia", "60 days per entry, and 90 days in any 180"),
                      ("Ukraine, EU, UK, US and most other visa-free passports", "90 days in any 180")],
            "faq": [
                ("Does leaving Turkey reset the count?", "No. The 180 days look back from each day, so a short trip out does not give you a new 90. For Russian citizens a new entry does start a new 60, but within what the 90 in 180 still allows."),
                ("An example?", "A Russian citizen spends 60 days in Turkey, leaves, and comes back ten days later. The 60 days are still in the last 180, so only 30 more are allowed — the calculator shows the exact last day."),
                ("How do I stay longer?", "With a residence permit, applied for in Turkey before your visa-free days run out."),
            ],
        },
        "ru": {
            "title": "Сколько можно находиться в Турции без визы — калькулятор 60 и 90/180",
            "description": "Сколько можно быть в Турции без визы? Россиянам — не больше 60 дней за въезд и 90 дней за любые 180, большинству безвизовых паспортов — 90 за 180. Введите поездки и узнайте, до какого числа можно остаться.",
            "eyebrow": "Калькулятор дней в Турции",
            "h1": "Сколько вы можете оставаться в Турции?",
            "lede": "Турция считает 90 дней за любые 180, а гражданам России вдобавок нельзя оставаться дольше 60 дней за один въезд. Выберите паспорт, введите поездки и узнайте, до какого числа можно остаться.",
            "presets": [
                ("Россия: 60 дней за въезд, 90 за любые 180", {"perEntry": 60, "allowance": 90, "window": 180}),
                ("Украина, ЕС, Великобритания, США и большинство безвизовых паспортов: 90 дней за любые 180", {"allowance": 90, "window": 180}),
            ],
            "table": [("Россия", "60 дней за въезд и 90 дней за любые 180"),
                      ("Украина, ЕС, Великобритания, США и большинство других безвизовых паспортов", "90 дней за любые 180")],
            "faq": [
                ("Обнуляет ли выезд лимит?", "Нет. 180 дней отсчитываются назад от каждого дня, поэтому короткий выезд не даёт новых 90. Для граждан России новый въезд начинает новые 60 дней, но только в пределах того, что ещё оставляют 90 за 180."),
                ("Пример?", "Гражданин России провёл в Турции 60 дней, выехал и вернулся через десять дней. Эти 60 дней ещё в последних 180, поэтому можно только 30 — калькулятор покажет точную последнюю дату."),
                ("Как остаться дольше?", "С видом на жительство: подать на него нужно в Турции, пока безвизовые дни не закончились."),
            ],
        },
    },
    {
        "key": "montenegro", "mode": "stay",
        "slug": {"en": "montenegro-stay-calculator/", "ru": "ru/kalkulyator-dnej-chernogoriya/"},
        "en": {
            "title": "Montenegro Stay Calculator — 90/180, and visas for Russians from 1 November 2026",
            "description": "How long can you stay in Montenegro? 90 days in any 180 for EU, UK and US passports. Russian citizens need a visa from 1 November 2026. Enter your trips and see the last day you can stay.",
            "eyebrow": "Montenegro stay calculator",
            "h1": "How long can you stay in Montenegro?",
            "lede": "Most visa-free passports may spend 90 days in any 180 in Montenegro. Since 1 November 2026 Russian citizens need a visa, and its own limit applies — enter it as your own rule.",
            "presets": [("EU, UK, US and most visa-free passports: 90 days in any 180", {"allowance": 90, "window": 180})],
            "table": [("EU, Schengen states, UK, US and most other visa-free passports", "90 days in any 180"),
                      ("Russia", "A visa from 1 November 2026: the days and entries printed on it")],
            "faq": [
                ("Do Russians still enter without a visa?", "No. Montenegro ended visa-free entry for Russian citizens on 31 October 2026; from 1 November a visa is needed. The visa states how many days it allows — choose “My own rule” and enter them."),
                ("Does leaving Montenegro reset the 90 days?", "No. On any day in Montenegro, the 180 days ending that day may hold at most 90 there, however many times you crossed the border."),
                ("Do Schengen days count?", "No. Montenegro is not in the Schengen area and counts its own days."),
            ],
        },
        "ru": {
            "title": "Сколько можно находиться в Черногории — калькулятор дней и визы для россиян с 1 ноября 2026",
            "description": "Сколько можно быть в Черногории? Паспортам ЕС, Великобритании и США — 90 дней за любые 180. Россиянам с 1 ноября 2026 нужна виза. Введите поездки и узнайте, до какого числа можно остаться.",
            "eyebrow": "Калькулятор дней в Черногории",
            "h1": "Сколько вы можете оставаться в Черногории?",
            "lede": "Большинству безвизовых паспортов в Черногории можно провести 90 дней за любые 180. С 1 ноября 2026 года гражданам России нужна виза, и действует её срок — введите его как своё правило.",
            "presets": [("ЕС, Великобритания, США и большинство безвизовых паспортов: 90 дней за любые 180", {"allowance": 90, "window": 180})],
            "table": [("ЕС, страны Шенгена, Великобритания, США и большинство других безвизовых паспортов", "90 дней за любые 180"),
                      ("Россия", "С 1 ноября 2026 — виза: сколько дней и въездов в ней указано")],
            "faq": [
                ("Россияне ещё въезжают без визы?", "Нет. Черногория прекратила безвизовый въезд для граждан России 31 октября 2026 года, с 1 ноября нужна виза. В визе указано, сколько дней она даёт, — выберите «Своё правило» и введите их."),
                ("Обнуляет ли выезд 90 дней?", "Нет. В любой день в Черногории из 180 дней, заканчивающихся этим днём, в Черногории может быть не больше 90, сколько бы раз вы ни пересекали границу."),
                ("Считаются ли дни в Шенгене?", "Нет. Черногория не входит в Шенген и считает свои дни отдельно."),
            ],
        },
    },
]

# MARK: - Writing

def esc(text):
    return html.escape(text, quote=True)


def rule_attrs(rule):
    names = {"perEntry": "data-per-entry", "allowance": "data-allowance", "window": "data-window",
             "threshold": "data-threshold", "start": "data-start"}
    return " ".join(f'{names[k]}="{esc(str(v))}"' for k, v in rule.items())


def custom_fields(page, c):
    if page["mode"] == "tax":
        return f'''
        <div class="rule-custom" data-custom hidden>
          <label><span>{c["threshold"]}</span><input type="number" inputmode="numeric" min="1" max="366" name="threshold" value="183"></label>
        </div>'''
    return f'''
        <div class="rule-custom" data-custom hidden>
          <label><span>{c["perEntry"]}</span><input type="number" inputmode="numeric" min="1" name="perEntry" placeholder="30"></label>
          <label><span>{c["allowance"]}</span><input type="number" inputmode="numeric" min="1" name="allowance" placeholder="90"></label>
          <label><span>{c["window"]}</span><input type="number" inputmode="numeric" min="1" name="window" placeholder="180"></label>
        </div>'''


def custom_label(page, lang, c):
    if page["mode"] == "tax":
        return "Своё: порог за любые 12 месяцев" if lang == "ru" else "My own: a threshold over any 12 months"
    return c["custom"]


def page_html(page, lang):
    c, p = COMMON[lang], page[lang]
    other = "ru" if lang == "en" else "en"
    slug = page["slug"][lang]
    depth = slug.count("/")
    up = "../" * depth
    url = SITE + slug

    options = "\n".join(
        f'            <option value="{i}" {rule_attrs(rule)}>{esc(label)}</option>'
        for i, (label, rule) in enumerate(p["presets"]))
    options += f'\n            <option value="custom">{esc(custom_label(page, lang, c))}</option>'

    table = ""
    if "table" in p:
        rows = "\n".join(f"            <tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in p["table"])
        head = ("<th>Паспорт</th><th>Сколько можно</th>" if lang == "ru" else "<th>Passport</th><th>How long</th>")
        table = f'''
        <table class="rules-table">
          <thead><tr>{head}</tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>'''

    faq = "\n\n".join(f"        <h3>{esc(q)}</h3>\n        <p>{esc(a)}</p>" for q, a in p["faq"])
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebApplication", "name": p["eyebrow"], "url": url,
             "applicationCategory": "TravelApplication", "operatingSystem": "Any", "inLanguage": lang,
             "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in p["faq"]]},
        ],
    }

    shots = "\n".join(f'''          <figure>
            <img src="{up}{c["shotsDir"]}{f}" width="570" height="1238" loading="lazy"
                 alt="{esc(alt)}">
            <figcaption>{esc(cap)}</figcaption>
          </figure>''' for f, alt, cap in c["shots"])

    related = [(c["schengen"], "ru/kalkulyator-shengena/" if lang == "ru" else "schengen-calculator/")]
    related += [(q[lang]["eyebrow"], q["slug"][lang]) for q in PAGES if q is not page]
    related_html = "\n".join(f'          <li><a href="{up}{href}">{esc(name)}</a></li>' for name, href in related)

    return f'''<!doctype html>
<!-- Written by tools/build-pages.py; change it there. -->
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(p["title"])}</title>
  <meta name="description" content="{esc(p["description"])}">
  <meta name="apple-itunes-app" content="app-id=6813907705">
  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="en" href="{SITE + page["slug"]["en"]}">
  <link rel="alternate" hreflang="ru" href="{SITE + page["slug"]["ru"]}">
  <link rel="alternate" hreflang="x-default" href="{SITE + page["slug"]["en"]}">
  <meta property="og:title" content="{esc(p["eyebrow"])}">
  <meta property="og:description" content="{esc(p["description"])}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <link rel="stylesheet" href="{up}styles.css">
  <script src="{up}stay.js" defer></script>
  <script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
  </script>
</head>
<body>
  <main class="shell">
    <nav aria-label="{c["nav"]}">
      <a class="brand" href="{up}">Presence</a>
      <div class="nav-links">
        <a href="{up}{page["slug"][other]}" hreflang="{other}" lang="{other}">{c["lang"]}</a>
        <a href="{up}pro/">Pro</a>
        <a href="{up}support/">{c["support"]}</a>
      </div>
    </nav>

    <header>
      <p class="eyebrow">{esc(p["eyebrow"])}</p>
      <h1>{esc(p["h1"])}</h1>
      <p class="lede">{esc(p["lede"])}</p>
    </header>

    <section id="calculator" class="calc" data-mode="{page["mode"]}" data-store="{page["key"]}" aria-label="{esc(p["eyebrow"])}">
      <article>
        <label class="rule-picker">
          <span>{c["rule"]}</span>
          <select data-rule>
{options}
          </select>
        </label>{custom_fields(page, c)}

        <h2>{c["trips"]}</h2>
        <p class="meta">{c["tripsHint"]}</p>
        <div class="trip-list" data-trips></div>
        <button type="button" class="button-quiet" data-add>{c["add"]}</button>

        <label class="check-date">
          <span>{c["check"]}</span>
          <input type="date" data-check>
          <small>{c["checkHint"]}</small>
        </label>
      </article>

      <article class="calc-result" aria-live="polite" data-result></article>
    </section>

    <section class="cta" aria-label="Presence">
      <article>
        <h2>{c["ctaTitle"]}</h2>
        <p>{c["cta"]}</p>
        <a class="button" href="https://apps.apple.com/app/id6813907705">{c["button"]}</a>
        <div class="gallery app-shots">
{shots}
        </div>
      </article>
    </section>

    <section aria-label="FAQ">
      <article>{table}
{faq}

        <p class="meta">{esc(c["checked"].format(date=CHECKED[lang]))}</p>
      </article>
    </section>

    <section aria-label="{c["related"]}">
      <article>
        <h2>{c["related"]}</h2>
        <ul class="related">
{related_html}
        </ul>
      </article>
    </section>

    <footer><a href="{up}">Presence</a> · <a href="{up}privacy/">{c["privacy"]}</a> · © 2026 Presence</footer>
  </main>
</body>
</html>
'''


def main():
    for page in PAGES:
        for lang in ("en", "ru"):
            out = ROOT / page["slug"][lang] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page_html(page, lang), encoding="utf-8")
            print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
